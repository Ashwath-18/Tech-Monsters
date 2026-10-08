import os
import json
import re
import io
import time
import logging
import concurrent.futures
from typing import Dict, Any, List, Optional
from dotenv import load_dotenv
from PIL import Image

load_dotenv()
load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))
load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

logger = logging.getLogger("gemma_client")
if not logger.handlers:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")

# Custom Exception Hierarchy
class GemmaError(Exception):
    """Base exception for Gemma client errors."""
    pass

class GemmaTimeoutError(GemmaError):
    """Raised when Gemma vision or language model request times out."""
    pass

class GemmaAPIError(GemmaError):
    """Raised on upstream 5xx, 4xx, quota exhaustion, or service connection errors."""
    def __init__(self, message: str, status_code: Optional[int] = None):
        super().__init__(message)
        self.status_code = status_code

class GemmaBadJSONError(GemmaError):
    """Raised when Gemma model response cannot be parsed into valid netlist JSON."""
    pass

class GemmaUnsupportedComponentError(GemmaError):
    """Raised when extracted netlist contains non-linear or non-supported components."""
    def __init__(self, message: str, netlist: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.netlist = netlist

# Setup GenAI client
def get_genai_client():
    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if not api_key:
        return None
    try:
        from google import genai
        return genai.Client(api_key=api_key)
    except Exception as e:
        logger.error(f"Failed to initialize GenAI client: {type(e).__name__}: {e}")
        return None

def get_model_name() -> str:
    return os.getenv("GEMMA_MODEL", "gemma-4-26b-a4b-it")

def get_timeout_s() -> float:
    try:
        return float(os.getenv("GEMMA_TIMEOUT_S", "45"))
    except (ValueError, TypeError):
        return 45.0

def extract_http_status(e: Exception) -> Optional[int]:
    """Extracts integer HTTP status code from exception attributes or error string."""
    for attr in ("code", "status_code", "http_status"):
        val = getattr(e, attr, None)
        if isinstance(val, int) and 100 <= val <= 599:
            return val
        if isinstance(val, str) and val.isdigit() and 100 <= int(val) <= 599:
            return int(val)
    match = re.search(r'\b([45]\d\d)\b', str(e))
    if match:
        return int(match.group(1))
    return None

# 1. Image Preprocessing with Pillow
def preprocess_image(image_bytes: bytes, max_dim: int = 1280, quality: int = 85) -> bytes:
    """
    Downscales image with Pillow: longest side at most 1280 px,
    converts to RGB, and re-encodes as JPEG quality 85.
    """
    try:
        img = Image.open(io.BytesIO(image_bytes))
        if img.mode != "RGB":
            img = img.convert("RGB")
        w, h = img.size
        longest = max(w, h)
        if longest > max_dim:
            scale = max_dim / float(longest)
            new_w = max(1, int(round(w * scale)))
            new_h = max(1, int(round(h * scale)))
            img = img.resize((new_w, new_h), Image.Resampling.LANCZOS)
        out = io.BytesIO()
        img.save(out, format="JPEG", quality=quality)
        return out.getvalue()
    except Exception as e:
        logger.warning(f"Pillow image preprocessing warning: {e}. Using raw image bytes.")
        return image_bytes

EXTRACTION_SYSTEM_PROMPT = """You are an expert electrical engineering schematic reader.
You will analyze a photo of a hand-drawn DC circuit schematic and extract its exact circuit netlist.

STRICT RULES:
1. ONLY linear DC components are supported:
   - Resistor: type "R", value in Ohms (e.g., 4.7k -> 4700, 1M -> 1000000, 100 -> 100).
   - Independent Voltage Source (or Battery): type "V", value in Volts (e.g., 12V -> 12, 5V -> 5).
     A battery or any DC voltage source must ALWAYS be type "V" with id "V1" (or "V2"...), and its drawn symbol/label goes in an optional "label" field (e.g., label: "E").
   - Independent Current Source: type "I", value in Amps (e.g., 2mA -> 0.002, 10uA -> 0.00001, 1A -> 1).
2. CURRENT ARROWS VS CURRENT SOURCES:
   - Arrows labeled I, I1, I2 drawn beside a wire or branch are current ANNOTATIONS, NOT current sources! Do NOT create components for them!
   - A current source is drawn explicitly as a circle containing an arrow, placed in the circuit path.
3. SYMBOLIC VALUES:
   - If a component's value is not a number in the drawing (e.g., labeled symbolically as 'E', 'R1', 'R2'), you MUST return "value": null, store the drawn label in "label", and list the symbol in a top-level "symbolic" list (e.g., ["E", "R1", "R2"]).
   - NEVER guess or assign default numeric values.
4. Ground node MUST ALWAYS be named "0". If no explicit ground symbol is drawn, choose the negative terminal of the main source or bottom common rail as "0".
5. Other nodes MUST be named "N1", "N2", "N3", etc.
6. For Voltage Sources (V), the nodes list must be [positive_node, negative_node].
7. For Current Sources (I), current flows through the source from nodes[0] to nodes[1] (arrow direction).
8. Return ONLY a valid JSON object matching this schema.

JSON SCHEMA:
{
  "components": [
    {"id": "V1", "type": "V", "value": null, "label": "E", "nodes": ["N1", "0"]},
    {"id": "R1", "type": "R", "value": null, "label": "R1", "nodes": ["N1", "0"]},
    {"id": "R2", "type": "R", "value": null, "label": "R2", "nodes": ["N1", "0"]}
  ],
  "symbolic": ["E", "R1", "R2"],
  "uncertain": ["brief note if any connection is ambiguous"]
}"""

# Unsupported Component Detection
SUPPORTED_TYPES = {"R", "V", "I"}
UNSUPPORTED_KEYWORDS = [
    "led", "diode", "transistor", "bjt", "mosfet", "fet", "igbt",
    "capacitor", "inductor", "opamp", "op-amp", "operational amplifier",
    "transformer", "switch", "ac source", "relay", "555", "ic", "integrated circuit"
]

def check_unsupported_components(netlist: Optional[Dict[str, Any]]) -> Optional[str]:
    """
    Returns an error message if the netlist components or uncertain notes explicitly
    name non-linear or unsupported components (LEDs, Diodes, Capacitors, Inductors, Transistors, Op-amps, etc.).
    UNSUPPORTED_COMPONENT is decided by component TYPE only, never by the id/name prefix.
    """
    if not isinstance(netlist, dict):
        return None

    components = netlist.get("components", [])
    for comp in components:
        comp_type = str(comp.get("type", "")).strip().upper()
        if comp_type and comp_type not in SUPPORTED_TYPES:
            return f"Component {comp.get('id', 'unknown')} has unsupported type '{comp_type}'. Only DC Resistors (R), Voltage Sources (V), and Current Sources (I) are supported."

    uncertain = netlist.get("uncertain", [])
    for item in uncertain:
        text = str(item).lower()
        for kw in UNSUPPORTED_KEYWORDS:
            if re.search(r'\b' + re.escape(kw) + r'\b', text):
                return f"Schematic contains unsupported element ({kw.upper()}): '{item}'. Only linear DC circuits (R, V, I) are supported."

    return None

def clean_and_parse_json(text: str) -> Optional[Dict[str, Any]]:
    """Strips markdown code fences and parses JSON robustly."""
    if not text:
        return None
    cleaned = text.strip()
    cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\s*```$", "", cleaned)
    cleaned = cleaned.strip()

    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        start = cleaned.find("{")
        end = cleaned.rfind("}")
        if start != -1 and end != -1 and end > start:
            try:
                return json.loads(cleaned[start:end + 1])
            except Exception:
                pass
        return None

def _invoke_model_call(client: Any, model_name: str, contents: list, config: Any, timeout_s: float) -> str:
    """Invokes generate_content on a background thread with explicit timeout_s limit."""
    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
        future = executor.submit(client.models.generate_content, model=model_name, contents=contents, config=config)
        try:
            response = future.result(timeout=timeout_s)
            return response.text or ""
        except concurrent.futures.TimeoutError:
            raise GemmaTimeoutError(f"Gemma model '{model_name}' timed out after {timeout_s}s.")
        except Exception as e:
            err_str = str(e).lower()
            if "timeout" in err_str or "timed out" in err_str or "deadline" in err_str:
                raise GemmaTimeoutError(f"Gemma model request timed out: {e}")
            status = extract_http_status(e)
            if status:
                raise GemmaAPIError(f"HTTP {status}: {e}", status_code=status)
            raise GemmaAPIError(f"API Error ({type(e).__name__}): {e}")

def _is_retryable_error(err: Exception) -> bool:
    """Returns True only for timeout, HTTP 429, and HTTP 5xx."""
    if isinstance(err, GemmaTimeoutError):
        return True
    if isinstance(err, GemmaAPIError):
        if err.status_code == 429:
            return True
        if err.status_code and 500 <= err.status_code <= 599:
            return True
    return False

def extract_netlist_from_image(image_bytes: bytes, mime_type: str = "image/jpeg") -> Dict[str, Any]:
    """
    Downscales image, calls Gemma multimodal vision with timeout and retry,
    logs telemetry, enforces JSON mode, and validates linear DC components.
    """
    client = get_genai_client()
    if not client:
        raise GemmaAPIError("GEMINI_API_KEY is not configured in .env or environment.")

    before_size = len(image_bytes)
    processed_bytes = preprocess_image(image_bytes, max_dim=1280, quality=85)
    after_size = len(processed_bytes)
    timeout_s = get_timeout_s()

    preferred_model = get_model_name()
    candidate_models = [preferred_model, "gemma-4-26b-a4b-it", "gemini-3.5-flash", "gemini-3.5-flash-lite"]
    models_to_try = [m for m in dict.fromkeys(candidate_models) if m]

    from google.genai import types
    image_part = types.Part.from_bytes(data=processed_bytes, mime_type="image/jpeg")
    prompt = "Extract the complete DC circuit netlist as strict JSON from this hand-drawn schematic."

    config = types.GenerateContentConfig(
        system_instruction=EXTRACTION_SYSTEM_PROMPT,
        temperature=0.1,
        response_mime_type="application/json"
    )

    last_error: Optional[Exception] = None

    for model_name in models_to_try:
        # Max 2 attempts per model (1 retry on timeout, 429, or 5xx)
        for attempt in range(1, 3):
            t0 = time.time()
            try:
                raw_text = _invoke_model_call(client, model_name, [image_part, prompt], config, timeout_s)
                latency = time.time() - t0
                logger.info(
                    "Gemma API call succeeded | Model: %s (attempt %d) | Image: %d -> %d bytes | Latency: %.2fs | Response: %s",
                    model_name, attempt, before_size, after_size, latency, raw_text[:300]
                )

                parsed = clean_and_parse_json(raw_text)
                if parsed is None:
                    # Retry once specifically for JSON parse failure
                    retry_prompt = f"Your previous response was not valid JSON. Response was:\n{raw_text}\nPlease convert it into valid JSON matching the exact schema."
                    retry_text = _invoke_model_call(client, model_name, [retry_prompt], config, timeout_s)
                    parsed = clean_and_parse_json(retry_text)

                if parsed is None:
                    raise GemmaBadJSONError(f"Model '{model_name}' response could not be parsed into valid JSON.")

                # Check for unsupported non-linear components
                unsupported_err = check_unsupported_components(parsed)
                if unsupported_err:
                    raise GemmaUnsupportedComponentError(unsupported_err, netlist=parsed)

                return parsed

            except GemmaUnsupportedComponentError as err:
                latency = time.time() - t0
                logger.error(
                    "Gemma API call unsupported component | Model: %s | Latency: %.2fs | Error: %s",
                    model_name, latency, str(err)
                )
                raise err

            except (GemmaTimeoutError, GemmaAPIError, GemmaBadJSONError) as err:
                latency = time.time() - t0
                last_error = err
                logger.error(
                    "Gemma API call failed | Model: %s (attempt %d) | Image: %d -> %d bytes | Latency: %.2fs | Error [%s]: %s",
                    model_name, attempt, before_size, after_size, latency, type(err).__name__, str(err)
                )

                # For 400/401/403 or non-retryable 4xx, fail immediately without retry
                if isinstance(err, GemmaAPIError) and err.status_code in (400, 401, 403):
                    raise err

                # Only retry on timeout, 429, or 5xx
                if _is_retryable_error(err):
                    if attempt == 1:
                        time.sleep(1.0)
                        continue
                break

            except Exception as err:
                latency = time.time() - t0
                status = extract_http_status(err)
                last_error = GemmaAPIError(f"HTTP {status}: {err}" if status else str(err), status_code=status)
                logger.error(
                    "Gemma API call unexpected error | Model: %s (attempt %d) | Image: %d -> %d bytes | Latency: %.2fs | Error [%s]: %s",
                    model_name, attempt, before_size, after_size, latency, type(err).__name__, str(err)
                )
                if status in (400, 401, 403):
                    raise last_error
                if _is_retryable_error(last_error):
                    if attempt == 1:
                        time.sleep(1.0)
                        continue
                break

    if isinstance(last_error, (GemmaTimeoutError, GemmaBadJSONError, GemmaUnsupportedComponentError, GemmaAPIError)):
        raise last_error
    raise GemmaAPIError(f"Model extraction failed across candidates {models_to_try}: {last_error}")

def repair_netlist_from_image(
    image_bytes: bytes,
    previous_netlist: Dict[str, Any],
    validation_errors: List[str],
    mime_type: str = "image/jpeg"
) -> Dict[str, Any]:
    """
    Prompts Gemma to repair netlist using validation feedback with timeout & retry.
    """
    client = get_genai_client()
    if not client:
        raise GemmaAPIError("GEMINI_API_KEY is not configured.")

    before_size = len(image_bytes)
    processed_bytes = preprocess_image(image_bytes, max_dim=1280, quality=85)
    after_size = len(processed_bytes)
    timeout_s = get_timeout_s()

    preferred_model = get_model_name()
    candidate_models = [preferred_model, "gemma-4-26b-a4b-it", "gemini-3.5-flash", "gemini-3.5-flash-lite"]
    models_to_try = [m for m in dict.fromkeys(candidate_models) if m]

    from google.genai import types
    image_part = types.Part.from_bytes(data=processed_bytes, mime_type="image/jpeg")

    errors_text = "\n".join(f"- {err}" for err in validation_errors)
    prompt = f"""The previous netlist extracted from this schematic failed electrical validation with the following specific problems:
{errors_text}

Previous extracted netlist:
{json.dumps(previous_netlist, indent=2)}

Please re-examine the schematic image carefully, fix the errors listed above (such as missing ground '0', floating dangling nodes, mislabeled junctions, or incorrect component values), and output ONLY the corrected valid JSON netlist."""

    config = types.GenerateContentConfig(
        system_instruction=EXTRACTION_SYSTEM_PROMPT,
        temperature=0.1,
        response_mime_type="application/json"
    )

    last_error: Optional[Exception] = None

    for model_name in models_to_try:
        for attempt in range(1, 3):
            t0 = time.time()
            try:
                raw_text = _invoke_model_call(client, model_name, [image_part, prompt], config, timeout_s)
                latency = time.time() - t0
                logger.info(
                    "Gemma Repair call succeeded | Model: %s (attempt %d) | Image: %d -> %d bytes | Latency: %.2fs | Response: %s",
                    model_name, attempt, before_size, after_size, latency, raw_text[:300]
                )

                parsed = clean_and_parse_json(raw_text)
                if parsed is None:
                    retry_prompt = f"Your previous repair response was not valid JSON:\n{raw_text}\nPlease return valid JSON matching the schema."
                    retry_text = _invoke_model_call(client, model_name, [retry_prompt], config, timeout_s)
                    parsed = clean_and_parse_json(retry_text)

                if parsed is None:
                    raise GemmaBadJSONError(f"Repair response on '{model_name}' was not valid JSON.")

                unsupported_err = check_unsupported_components(parsed)
                if unsupported_err:
                    raise GemmaUnsupportedComponentError(unsupported_err, netlist=parsed)

                return parsed

            except GemmaUnsupportedComponentError as err:
                latency = time.time() - t0
                logger.error(
                    "Gemma Repair call unsupported component | Model: %s | Latency: %.2fs | Error: %s",
                    model_name, latency, str(err)
                )
                raise err

            except (GemmaTimeoutError, GemmaAPIError, GemmaBadJSONError) as err:
                latency = time.time() - t0
                last_error = err
                logger.error(
                    "Gemma Repair call failed | Model: %s (attempt %d) | Latency: %.2fs | Error [%s]: %s",
                    model_name, attempt, latency, type(err).__name__, str(err)
                )
                if isinstance(err, GemmaAPIError) and err.status_code in (400, 401, 403):
                    raise err
                if _is_retryable_error(err):
                    if attempt == 1:
                        time.sleep(1.0)
                        continue
                break

            except Exception as err:
                latency = time.time() - t0
                status = extract_http_status(err)
                last_error = GemmaAPIError(f"HTTP {status}: {err}" if status else str(err), status_code=status)
                if status in (400, 401, 403):
                    raise last_error
                if _is_retryable_error(last_error):
                    if attempt == 1:
                        time.sleep(1.0)
                        continue
                break

    if isinstance(last_error, (GemmaTimeoutError, GemmaBadJSONError, GemmaUnsupportedComponentError, GemmaAPIError)):
        raise last_error
    raise GemmaAPIError(f"Repair model failed across candidates {models_to_try}: {last_error}")

def explain_student_mistake(
    netlist: Dict[str, Any],
    solved_data: Dict[str, Any],
    student_claim: str
) -> str:
    """
    Explains in pedagogical language why the student's answer was correct or incorrect.
    Includes fallback models and deterministic circuit diagnostic fallback.
    """
    client = get_genai_client()
    if client:
        preferred_model = get_model_name()
        candidate_models = [preferred_model, "gemma-4-26b-a4b-it", "gemini-3.5-flash", "gemini-3.5-flash-lite"]
        models_to_try = [m for m in dict.fromkeys(candidate_models) if m]
        timeout_s = get_timeout_s()

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

        config = types.GenerateContentConfig(temperature=0.2)
        for model_name in models_to_try:
            try:
                resp_text = _invoke_model_call(client, model_name, [prompt], config, timeout_s)
                if resp_text and resp_text.strip():
                    return resp_text.strip()
            except Exception:
                continue

    # Deterministic engineering diagnostic fallback
    voltages = solved_data.get("node_voltages", {})
    comps = solved_data.get("components", [])

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
