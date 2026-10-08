import os
import json
import re
from typing import Dict, Any, List, Optional
from dotenv import load_dotenv

load_dotenv()
load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))
load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

# Setup GenAI client
def get_genai_client():
    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if not api_key:
        return None
    try:
        from google import genai
        return genai.Client(api_key=api_key)
    except Exception as e:
        print(f"Failed to initialize GenAI client: {e}")
        return None

def get_model_name() -> str:
    return os.getenv("GEMMA_MODEL", "gemini-2.5-flash")

EXTRACTION_SYSTEM_PROMPT = """You are an expert electrical engineering schematic reader.
You will analyze a photo of a hand-drawn DC circuit schematic and extract its exact circuit netlist.

STRICT RULES:
1. ONLY DC components are supported:
   - Resistor: type "R", value in Ohms (e.g., 4.7k -> 4700, 1M -> 1000000, 100 -> 100)
   - Independent Voltage Source: type "V", value in Volts (e.g., 12V -> 12, 5V -> 5)
   - Independent Current Source: type "I", value in Amps (e.g., 2mA -> 0.002, 10uA -> 0.00001, 1A -> 1)
2. Ground node MUST ALWAYS be named "0". If no explicit ground symbol is drawn, choose the negative terminal of the main source or bottom common rail as "0".
3. Other nodes MUST be named "N1", "N2", "N3", etc.
4. For Voltage Sources (V), the nodes list must be [positive_node, negative_node].
5. For Current Sources (I), current flows through the source from nodes[0] to nodes[1] (arrow direction).
6. Return ONLY a valid JSON object matching this schema, with NO conversational text, NO explanations, and NO markdown code fences.

JSON SCHEMA:
{
  "components": [
    {"id": "V1", "type": "V", "value": 12.0, "nodes": ["N1", "0"]},
    {"id": "R1", "type": "R", "value": 1000.0, "nodes": ["N1", "N2"]},
    {"id": "R2", "type": "R", "value": 2000.0, "nodes": ["N2", "0"]}
  ],
  "uncertain": ["brief note if any component value, label, or junction connection is ambiguous"]
}"""

def clean_and_parse_json(text: str) -> Optional[Dict[str, Any]]:
    """Strips markdown code fences and parses JSON robustly."""
    if not text:
        return None
    cleaned = text.strip()
    # Remove markdown code fences if present
    cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\s*```$", "", cleaned)
    cleaned = cleaned.strip()

    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        # Try finding the first '{' and last '}'
        start = cleaned.find("{")
        end = cleaned.rfind("}")
        if start != -1 and end != -1 and end > start:
            try:
                return json.loads(cleaned[start:end + 1])
            except Exception:
                pass
        return None

def extract_netlist_from_image(image_bytes: bytes, mime_type: str = "image/jpeg") -> Dict[str, Any]:
    """
    Calls Gemma / Gemini model via google-genai to extract circuit netlist.
    Includes automatic fallback models and retry for resilience.
    """
    client = get_genai_client()
    if not client:
        raise RuntimeError("GEMINI_API_KEY is not configured in .env or environment.")

    preferred_model = get_model_name()
    candidate_models = [preferred_model, "gemini-2.5-flash", "gemini-2.0-flash"]
    # De-duplicate while preserving order
    models_to_try = [m for m in dict.fromkeys(candidate_models) if m not in ("gemini-3.8-flash", "gemini-1.5-flash")]
    if not models_to_try:
        models_to_try = ["gemini-2.5-flash", "gemini-2.0-flash"]

    from google.genai import types
    image_part = types.Part.from_bytes(data=image_bytes, mime_type=mime_type)
    prompt = "Extract the complete DC circuit netlist as strict JSON from this hand-drawn schematic."

    last_error = None
    for model_name in models_to_try:
        for attempt in range(2):
            try:
                response = client.models.generate_content(
                    model=model_name,
                    contents=[image_part, prompt],
                    config=types.GenerateContentConfig(
                        system_instruction=EXTRACTION_SYSTEM_PROMPT,
                        temperature=0.1
                    )
                )
                parsed = clean_and_parse_json(response.text)
                if parsed is not None:
                    return parsed

                # Retry once if not valid JSON
                retry_prompt = f"Your previous response was not valid JSON. Response was:\n{response.text}\nPlease convert it into valid JSON matching the exact schema."
                retry_resp = client.models.generate_content(
                    model=model_name,
                    contents=[retry_prompt],
                    config=types.GenerateContentConfig(temperature=0.0)
                )
                parsed = clean_and_parse_json(retry_resp.text)
                if parsed is not None:
                    return parsed
            except Exception as e:
                last_error = e
                import time
                time.sleep(1.0)
                continue

    raise ValueError(f"Model extraction failed across candidates {models_to_try}: {last_error}")

def repair_netlist_from_image(
    image_bytes: bytes,
    previous_netlist: Dict[str, Any],
    validation_errors: List[str],
    mime_type: str = "image/jpeg"
) -> Dict[str, Any]:
    """
    Asks the model to repair the netlist given the exact deterministic validation errors.
    """
    client = get_genai_client()
    if not client:
        raise RuntimeError("GEMINI_API_KEY is not configured.")

    model_name = get_model_name()
    from google.genai import types

    image_part = types.Part.from_bytes(data=image_bytes, mime_type=mime_type)

    errors_text = "\n".join(f"- {err}" for err in validation_errors)
    prompt = f"""The previous netlist extracted from this schematic failed electrical validation with the following specific problems:
{errors_text}

Previous extracted netlist:
{json.dumps(previous_netlist, indent=2)}

Please re-examine the schematic image carefully, fix the errors listed above (such as missing ground '0', floating dangling nodes, mislabeled junctions, or incorrect component values), and output ONLY the corrected valid JSON netlist."""

    preferred_model = get_model_name()
    candidate_models = [preferred_model, "gemini-2.5-flash", "gemini-2.0-flash", "gemini-1.5-flash"]
    models_to_try = list(dict.fromkeys(candidate_models))

    last_error = None
    for model_name in models_to_try:
        try:
            response = client.models.generate_content(
                model=model_name,
                contents=[image_part, prompt],
                config=types.GenerateContentConfig(
                    system_instruction=EXTRACTION_SYSTEM_PROMPT,
                    temperature=0.1
                )
            )
            parsed = clean_and_parse_json(response.text)
            if parsed is not None:
                return parsed
        except Exception as e:
            last_error = e
            continue

    raise ValueError(f"Repair model failed across candidate models {models_to_try}: {last_error}")

def explain_student_mistake(
    netlist: Dict[str, Any],
    solved_data: Dict[str, Any],
    student_claim: str
) -> str:
    """
    Explains in clear, constructive pedagogical language why the student's answer was correct or incorrect.
    Includes multi-model fallback and deterministic circuit diagnostic fallback.
    """
    client = get_genai_client()
    if client:
        preferred_model = get_model_name()
        candidate_models = [preferred_model, "gemini-2.5-flash", "gemini-2.0-flash", "gemini-1.5-flash"]
        models_to_try = list(dict.fromkeys(candidate_models))

        from google.genai import types
        prompt = f"""A student solved this DC circuit and submitted their answer.
Circuit Netlist:
{json.dumps(netlist, indent=2)}

Exact Numerical MNA Solution:
- Node Voltages: {json.dumps(solved_data.get('node_voltages', {}))}
- Component Currents & Voltage Drops: {json.dumps(solved_data.get('components', []), indent=2)}

Student's Claimed Answer:
"{student_claim}"

Task:
1. State whether the student's calculation is correct or incorrect.
2. Explain concisely what the true answer is with the step-by-step formula.
3. Diagnose the likely conceptual mistake if incorrect (e.g. inverted divider ratio, wrong node reference, missed parallel rule)."""

        for model_name in models_to_try:
            try:
                response = client.models.generate_content(
                    model=model_name,
                    contents=[prompt],
                    config=types.GenerateContentConfig(temperature=0.2)
                )
                if response.text and response.text.strip():
                    return response.text.strip()
            except Exception:
                continue

    # Deterministic engineering diagnostic fallback
    voltages = solved_data.get("node_voltages", {})
    comps = solved_data.get("components", [])

    # Check for node match
    node_match = re.search(r"N(\d+)[^\d]*(\d+(?:\.\d+)?)", student_claim, re.IGNORECASE)
    if node_match:
        node_name = f"N{node_match.group(1)}"
        claimed_val = float(node_match.group(2))
        if node_name in voltages:
            actual_val = voltages[node_name]
            if abs(claimed_val - actual_val) < 0.05:
                return f"Correct! Node {node_name} potential is verified at {actual_val:.3f} V via Modified Nodal Analysis (KCL equilibrium satisfied)."
            else:
                return f"Not quite. Your calculation gave {claimed_val} V for Node {node_name}, but the exact solved potential is {actual_val:.3f} V. Review your voltage divider ratio or check KVL around the loop containing Node {node_name}."

    # Check for component current match
    comp_match = re.search(r"(R\d+|V\d+|I\d+)[^\d]*(\d+(?:\.\d+)?)\s*(m?A)?", student_claim, re.IGNORECASE)
    if comp_match:
        comp_id = comp_match.group(1).upper()
        claimed_val = float(comp_match.group(2))
        is_milli = comp_match.group(3) and comp_match.group(3).lower() == "ma" or "ma" in student_claim.lower()
        if is_milli and claimed_val > 0.05:
            claimed_val /= 1000.0

        target = next((c for c in comps if c.get("id") == comp_id), None)
        if target:
            actual_curr = target.get("current", 0.0)
            v_drop = target.get("voltage_drop", 0.0)
            r_val = target.get("value", 1.0)
            if abs(claimed_val - actual_curr) < 0.0005:
                return f"Correct! The current through {comp_id} is exactly {actual_curr*1000:.3f} mA (Ohm's Law: I = ΔV / R = {v_drop:.2f}V / {r_val}Ω)."
            else:
                return f"Your current calculation of {comp_match.group(2)}{'mA' if is_milli else 'A'} for {comp_id} differs from the verified solution of {actual_curr*1000:.3f} mA. Ensure you calculate the branch voltage drop ΔV ({v_drop:.2f} V) rather than using total supply voltage."

    return f"Analyzed claim: '{student_claim}'. Ground reference is Node 0 (0.00 V). Compare your calculated values with the exact branch voltages and node potentials listed in the verified results table above."

