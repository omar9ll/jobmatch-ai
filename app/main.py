"""JobMatch AI: FastAPI app that scores a resume against a job posting."""

from __future__ import annotations

import io
from pathlib import Path

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from .llm import ai_suggestions
from .matcher import match

MAX_TEXT = 20_000
MAX_PDF_BYTES = 5 * 1024 * 1024
STATIC_DIR = Path(__file__).resolve().parent.parent / "static"

app = FastAPI(title="JobMatch AI", version="1.0.0")


class AnalyzeRequest(BaseModel):
    resume: str = Field(..., min_length=20, max_length=MAX_TEXT)
    job: str = Field(..., min_length=20, max_length=MAX_TEXT)


def analyze_text(resume: str, job: str) -> dict:
    result = match(resume, job)
    return {**result.to_dict(), **ai_suggestions(resume, job, result)}


def pdf_to_text(data: bytes) -> str:
    from pypdf import PdfReader

    try:
        reader = PdfReader(io.BytesIO(data))
        return "\n".join(page.extract_text() or "" for page in reader.pages)
    except Exception as exc:
        raise HTTPException(status_code=400, detail="Could not read that PDF.") from exc


@app.get("/api/health")
def health() -> dict:
    return {"status": "ok"}


@app.post("/api/analyze")
def analyze(req: AnalyzeRequest) -> dict:
    return analyze_text(req.resume, req.job)


@app.post("/api/analyze-pdf")
async def analyze_pdf(job: str = Form(..., min_length=20, max_length=MAX_TEXT), resume_pdf: UploadFile = File(...)) -> dict:
    if resume_pdf.content_type not in ("application/pdf", "application/octet-stream"):
        raise HTTPException(status_code=400, detail="Please upload a PDF.")
    data = await resume_pdf.read()
    if len(data) > MAX_PDF_BYTES:
        raise HTTPException(status_code=413, detail="PDF is larger than 5 MB.")
    text = pdf_to_text(data)
    if len(text.strip()) < 20:
        raise HTTPException(status_code=400, detail="No readable text found in that PDF.")
    return analyze_text(text[:MAX_TEXT], job)


@app.get("/")
def index() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")


app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
