# CircuitCheck

Photo of a hand-drawn DC circuit goes in, a verified analysis comes out.

## What it does
CircuitCheck is an automated pipeline that digitizes hand-drawn DC circuits, verifies their topological and electrical validity with deterministic checks, repairs ambiguities through a closed-loop LLM repair cycle, and calculates exact nodal voltages, branch currents, and component power using Modified Nodal Analysis (MNA). It also includes a student answer checker with pedagogical feedback.

## Architecture
1. **Multimodal Extraction (`/api/read`):** Calls Gemma 4 via the Google GenAI SDK to produce a strict JSON netlist without prose.
2. **Deterministic Validation (`validators.py`):** Checks for ground reference ("0"), floating nodes, valid component parameters, and voltage source loops.
3. **Closed-Loop Repair:** If validation fails, errors are fed back to Gemma for up to 2 repair rounds.
4. **MNA Solver (`solver.py`):** Pure numerical Modified Nodal Analysis using NumPy (never letting LLM compute numbers).
5. **Student Checker (`/api/check`):** Compares student claims against the ground-truth numerical solution and uses Gemma to explain mistakes.

## Where Gemma is used
- **Vision-to-Netlist Extraction:** Deciphers hand-drawn circuit schematics into a structured JSON netlist.
- **Self-Correction Feedback:** Re-evaluates ambiguous junctions and missing nodes when deterministic rules flag discrepancies.
- **Pedagogical Explanation:** Generates targeted explanations when a student's answer diverges from the MNA solution.

## Setup
### Backend
```bash
cd backend
python -m venv venv
# Windows:
.\venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate

pip install -r requirements.txt
cp ../.env.example .env # and add your GEMINI_API_KEY
uvicorn main:app --reload --port 8000
```

### Run Tests
```bash
pytest
```

## Honest Limitations
- DC circuits only (Resistors, Independent Voltage Sources, Independent Current Sources).
- No AC, capacitors, inductors, op-amps, or semiconductor devices (diodes/transistors).
- Extreme perspective distortion or severely overlapping handwriting may require human verification via the UI netlist editor.
