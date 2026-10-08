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
    explain_student_mistake
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
    1. Reads circuit image.
    2. Calls Gemma to extract JSON netlist.
    3. Runs deterministic validators.
    4. If validation fails, triggers closed-loop repair (max 2 rounds).
    5. Solves with Modified Nodal Analysis (MNA).
    """
    contents = await file.read()
    if not contents:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    mime_type = file.content_type or "image/jpeg"
    rounds_log: List[Dict[str, Any]] = []

    # Round 1: Initial Extraction
    try:
        netlist = extract_netlist_from_image(contents, mime_type=mime_type)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Gemma extraction error: {str(e)}")

    validation_errors = validate_netlist(netlist)
    rounds_log.append({
        "round": 1,
        "action": "initial_extraction",
        "netlist": netlist,
        "validation_errors": validation_errors,
        "passed": len(validation_errors) == 0
    })

    # Closed-loop Repair (Max 2 repair rounds)
    repair_count = 0
    max_repairs = 2

    while len(validation_errors) > 0 and repair_count < max_repairs:
        repair_count += 1
        try:
            netlist = repair_netlist_from_image(
                image_bytes=contents,
                previous_netlist=netlist,
                validation_errors=validation_errors,
                mime_type=mime_type
            )
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
    solved_result = None
    solver_error = None
    if len(validation_errors) == 0:
        try:
            solved_result = solve_circuit(netlist)
        except SolverError as se:
            solver_error = str(se)
    else:
        solver_error = "Circuit netlist failed validation checks."

    return {
        "is_valid": len(validation_errors) == 0 and solver_error is None,
        "final_netlist": netlist,
        "validation_errors": validation_errors,
        "solver_error": solver_error,
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

