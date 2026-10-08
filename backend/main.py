import os
import re
from typing import Dict, Any, List, Optional
from fastapi import FastAPI, UploadFile, File, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel

from validators import validate_netlist
from solver import solve_circuit, SolverError
from gemma_client import (
    extract_netlist_from_image,
    repair_netlist_from_image,
    explain_student_mistake,
    check_unsupported_components,
    GemmaTimeoutError,
    GemmaAPIError,
    GemmaBadJSONError,
    GemmaUnsupportedComponentError
)

app = FastAPI(title="CircuitCheck API", description="DC Circuit Multimodal Extractor & Verifier")

# Enable CORS for local dev
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class NetlistRequest(BaseModel):
    netlist: Dict[str, Any]

class CheckRequest(BaseModel):
    netlist: Dict[str, Any]
    solved: Optional[Dict[str, Any]] = None
    student_claim: str

@app.get("/health")
def health():
    return {"status": "ok", "service": "CircuitCheck"}

@app.post("/api/read")
async def read_circuit(file: UploadFile = File(...)):
    """
    1. Reads & downscales circuit image.
    2. Calls Gemma to extract JSON netlist with timeout & retries.
    3. Runs deterministic validators and closed-loop repair.
    4. Solves with Modified Nodal Analysis (MNA).
    5. Returns exact status code: OK, TIMEOUT, API_ERROR, BAD_JSON, UNSUPPORTED_COMPONENT, VALIDATION_FAILED.
    """
    contents = await file.read()
    if not contents:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    mime_type = file.content_type or "image/jpeg"
    rounds_log: List[Dict[str, Any]] = []

    # Round 1: Initial Extraction
    try:
        netlist = extract_netlist_from_image(contents, mime_type=mime_type)
    except GemmaTimeoutError as e:
        return {
            "code": "TIMEOUT",
            "message": str(e) or "Request to Gemma vision model timed out.",
            "is_valid": False,
            "final_netlist": None,
            "validation_errors": ["Extraction request timed out."],
            "solver_error": "Timeout during vision extraction.",
            "solved": None,
            "rounds_log": [{"round": 1, "action": "initial_extraction", "passed": False, "error": "TIMEOUT"}],
            "repairs_needed": 0
        }
    except GemmaBadJSONError as e:
        return {
            "code": "BAD_JSON",
            "message": str(e) or "Gemma model response was not valid netlist JSON.",
            "is_valid": False,
            "final_netlist": None,
            "validation_errors": ["Invalid JSON netlist returned."],
            "solver_error": "JSON parse error.",
            "solved": None,
            "rounds_log": [{"round": 1, "action": "initial_extraction", "passed": False, "error": "BAD_JSON"}],
            "repairs_needed": 0
        }
    except GemmaUnsupportedComponentError as e:
        return {
            "code": "UNSUPPORTED_COMPONENT",
            "message": str(e),
            "is_valid": False,
            "final_netlist": e.netlist,
            "validation_errors": [str(e)],
            "solver_error": "Unsupported non-linear or reactive component detected.",
            "solved": None,
            "rounds_log": [{"round": 1, "action": "initial_extraction", "passed": False, "error": "UNSUPPORTED_COMPONENT"}],
            "repairs_needed": 0
        }
    except GemmaAPIError as e:
        return {
            "code": "API_ERROR",
            "message": str(e) or "AI Vision API service error.",
            "is_valid": False,
            "final_netlist": None,
            "validation_errors": [str(e)],
            "solver_error": "Vision API failure.",
            "solved": None,
            "rounds_log": [{"round": 1, "action": "initial_extraction", "passed": False, "error": "API_ERROR"}],
            "repairs_needed": 0
        }
    except Exception as e:
        return {
            "code": "API_ERROR",
            "message": f"Unexpected digitization error: {str(e)}",
            "is_valid": False,
            "final_netlist": None,
            "validation_errors": [str(e)],
            "solver_error": str(e),
            "solved": None,
            "rounds_log": [{"round": 1, "action": "initial_extraction", "passed": False, "error": str(e)}],
            "repairs_needed": 0
        }

    # Verify linear DC components
    unsupported_msg = check_unsupported_components(netlist)
    if unsupported_msg:
        return {
            "code": "UNSUPPORTED_COMPONENT",
            "message": unsupported_msg,
            "is_valid": False,
            "final_netlist": netlist,
            "validation_errors": [unsupported_msg],
            "solver_error": "Circuit contains unsupported components.",
            "solved": None,
            "rounds_log": [{"round": 1, "action": "component_check", "passed": False, "error": unsupported_msg}],
            "repairs_needed": 0
        }

    # Check for symbolic / missing numeric values (VALUES_MISSING) BEFORE running validators
    components = netlist.get("components", []) if isinstance(netlist, dict) else []
    missing_symbols: List[str] = []
    symbolic_list = netlist.get("symbolic", []) if isinstance(netlist, dict) else []

    for comp in components:
        if comp.get("value") is None:
            lbl = comp.get("label") or comp.get("id")
            if lbl and lbl not in missing_symbols:
                missing_symbols.append(lbl)

    for sym in symbolic_list:
        if sym and sym not in missing_symbols:
            missing_symbols.append(sym)

    has_null_values = any(comp.get("value") is None for comp in components)
    has_symbolic_list = bool(symbolic_list and len(symbolic_list) > 0)

    if has_null_values or has_symbolic_list:
        sym_str = ", ".join(missing_symbols) if missing_symbols else "E, R1, R2"
        msg = f"The drawing has symbols but no numbers ({sym_str}). Enter values and re-simulate."
        return {
            "code": "VALUES_MISSING",
            "message": msg,
            "is_valid": False,
            "final_netlist": netlist,
            "validation_errors": [msg],
            "solver_error": None,
            "solved": None,
            "rounds_log": [{"round": 1, "action": "symbolic_check", "passed": False, "status": "VALUES_MISSING"}],
            "repairs_needed": 0
        }

    validation_errors = validate_netlist(netlist)
    rounds_log.append({
        "round": 1,
        "action": "initial_extraction",
        "netlist": netlist,
        "validation_errors": validation_errors,
        "passed": len(validation_errors) == 0
    })

    # Closed-loop Repair (1 repair round for speed)
    repair_count = 0
    max_repairs = 1

    while len(validation_errors) > 0 and repair_count < max_repairs:
        repair_count += 1
        try:
            netlist = repair_netlist_from_image(
                image_bytes=contents,
                previous_netlist=netlist,
                validation_errors=validation_errors,
                mime_type=mime_type
            )
            unsupported_msg = check_unsupported_components(netlist)
            if unsupported_msg:
                return {
                    "code": "UNSUPPORTED_COMPONENT",
                    "message": unsupported_msg,
                    "is_valid": False,
                    "final_netlist": netlist,
                    "validation_errors": [unsupported_msg],
                    "solver_error": "Circuit contains unsupported components.",
                    "solved": None,
                    "rounds_log": rounds_log,
                    "repairs_needed": repair_count
                }
            validation_errors = validate_netlist(netlist)
            rounds_log.append({
                "round": repair_count + 1,
                "action": f"repair_round_{repair_count}",
                "netlist": netlist,
                "validation_errors": validation_errors,
                "passed": len(validation_errors) == 0
            })
        except Exception as e:
            rounds_log.append({
                "round": repair_count + 1,
                "action": f"repair_round_{repair_count}_failed",
                "error": str(e),
                "passed": False
            })
            break

    # Solve if valid
    if len(validation_errors) > 0:
        return {
            "code": "VALIDATION_FAILED",
            "message": f"Circuit netlist failed electrical validation rules: {'; '.join(validation_errors)}",
            "is_valid": False,
            "final_netlist": netlist,
            "validation_errors": validation_errors,
            "solver_error": "Circuit netlist failed validation checks.",
            "solved": None,
            "rounds_log": rounds_log,
            "repairs_needed": repair_count
        }

    solved_result = None
    solver_error = None
    try:
        solved_result = solve_circuit(netlist)
    except SolverError as se:
        solver_error = str(se)

    if solver_error:
        return {
            "code": "VALIDATION_FAILED",
            "message": f"Numerical solver failed: {solver_error}",
            "is_valid": False,
            "final_netlist": netlist,
            "validation_errors": [solver_error],
            "solver_error": solver_error,
            "solved": None,
            "rounds_log": rounds_log,
            "repairs_needed": repair_count
        }

    return {
        "code": "OK",
        "message": f"Circuit verified and solved successfully with 0 errors.{f' (Fixed in {repair_count} repair round)' if repair_count else ''}",
        "is_valid": True,
        "final_netlist": netlist,
        "validation_errors": [],
        "solver_error": None,
        "solved": solved_result,
        "rounds_log": rounds_log,
        "repairs_needed": repair_count
    }


@app.post("/api/solve")
async def solve_manual_netlist(payload: NetlistRequest):
    """
    Validates and numerically solves a provided netlist JSON directly.
    """
    netlist = payload.netlist
    validation_errors = validate_netlist(netlist)
    if validation_errors:
        return {
            "is_valid": False,
            "validation_errors": validation_errors,
            "solved": None
        }

    try:
        solved = solve_circuit(netlist)
        return {
            "is_valid": True,
            "validation_errors": [],
            "solved": solved
        }
    except SolverError as e:
        return {
            "is_valid": False,
            "validation_errors": [str(e)],
            "solved": None
        }

@app.post("/api/check")
async def check_student_answer(payload: CheckRequest):
    """
    Compares the student's claimed answer against the exact MNA solution,
    and asks Gemma to provide pedagogical feedback if incorrect.
    """
    netlist = payload.netlist
    solved = payload.solved
    student_claim = payload.student_claim.strip()

    if not solved:
        # Re-solve if not provided
        val_errors = validate_netlist(netlist)
        if val_errors:
            raise HTTPException(status_code=400, detail="Cannot check answer: Netlist is invalid.")
        solved = solve_circuit(netlist)

    # Let's do basic numeric check heuristic if student claim mentions a number
    # E.g. "V(N2) = 4V" or "N2 = 4" or "current = 5mA"
    explanation = explain_student_mistake(netlist, solved, student_claim)

    return {
        "student_claim": student_claim,
        "solved_reference": solved,
        "explanation": explanation
    }

# Mount samples directory
samples_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "samples"))
if os.path.isdir(samples_dir):
    app.mount("/samples", StaticFiles(directory=samples_dir), name="samples")

# Mount frontend static files
frontend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "frontend"))
if os.path.isdir(frontend_dir):
    app.mount("/", StaticFiles(directory=frontend_dir, html=True), name="frontend")

