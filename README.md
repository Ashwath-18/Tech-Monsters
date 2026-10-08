# VyaparLens

Photo of a handwritten bill in, audited digital ledger out.

## Overview
VyaparLens digitizes messy real-world handwritten chits, kirana bills, and mandi receipts in Indian languages. It uses Gemma for multimodal extraction with a deterministic verification harness that validates line math, total sums, and flags anomalies.

## Where Gemma is used
Gemma extracts line items, handwritten quantities, units, and rates directly from photos of messy chits with field-level confidence flags, and participates in an automated correction feedback loop when deterministic checks flag discrepancies.

## Setup
### Backend
```bash
cd backend
python -m venv venv
# On Windows:
.\venv\Scripts\activate
# On Linux/macOS:
source venv/bin/activate

pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

### Frontend
Open `frontend/index.html` directly in a browser or serve with any static file server.
