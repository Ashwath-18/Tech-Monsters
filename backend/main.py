from fastapi import FastAPI, UploadFile

app = FastAPI(title="VyaparLens API")

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/extract")
async def extract(file: UploadFile):
    return {"todo": "call Gemma here", "filename": file.filename}
