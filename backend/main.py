import os
import logging
from dotenv import load_dotenv
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from llm_handler import analyze_resume
from matcher import compare_candidates, match_candidate
from models import CandidateComparisonRequest, CandidateProfile, JobRequirements
from resume_extractor import extract_resume_text

load_dotenv()

app = FastAPI(
    title="AI Resume–Job Requirement Matcher API",
    version="1.0.0",
    description="Resume extraction, structured AI analysis, and candidate matching.",
)

frontend_origin = os.getenv("FRONTEND_URL", "http://localhost:5173")
allowed_origins = list({
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    frontend_origin,
})

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)


@app.get("/")
def root():
    return {"message": "AI Resume–Job Matcher API is running."}


@app.get("/health")
def health():
    return {"status": "healthy"}


@app.post("/upload-resume")
async def upload_resume(file: UploadFile = File(...)):
    filename = file.filename or ""
    try:
        content = await file.read()
        text = extract_resume_text(content, filename)
        return {
            "status": "success",
            "filename": filename,
            "extracted_text": text,
            "character_count": len(text),
        }
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=422,
            detail="Could not read this document. Check that the file is valid and not corrupted.",
        ) from exc
    finally:
        await file.close()




@app.post("/analyze-resume")
def analyze_resume_endpoint(payload: dict):
    resume_text = payload.get("resume_text", "")

    if not isinstance(resume_text, str) or not resume_text.strip():
        raise HTTPException(
            status_code=400,
            detail="Resume text cannot be empty."
        )

    if len(resume_text) > 60000:
        raise HTTPException(
            status_code=413,
            detail="Extracted resume text is too long (maximum 60,000 characters)."
        )

    try:
        return {"status": "success", **analyze_resume(resume_text)}

    except RuntimeError as exc:
        logging.exception("Resume analysis failed.")
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    except Exception as exc:
        logging.exception("Unexpected error in resume analysis endpoint.")
        raise HTTPException(
            status_code=502,
            detail="Groq analysis failed. Check the backend terminal for details."
        ) from exc



@app.post("/match-candidate")
def match_single_candidate(payload: dict):
    try:
        candidate = CandidateProfile.model_validate(payload.get("candidate"))
        job = JobRequirements.model_validate(payload.get("job"))
        return {"status": "success", "match_report": match_candidate(candidate, job)}
    except Exception as exc:
        raise HTTPException(status_code=422, detail="Invalid candidate or job requirements.") from exc


@app.post("/compare-candidates")
def compare_candidates_endpoint(request: CandidateComparisonRequest):
    return {
        "status": "success",
        "job_title": request.job.job_title,
        "total_candidates": len(request.candidates),
        "candidates": compare_candidates(request.candidates, request.job),
    }
