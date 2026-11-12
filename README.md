# AI Resume–Job Requirement Matcher

A working MVP that extracts candidate information from PDF/DOCX resumes with Groq, validates the result using Pydantic, and compares multiple candidates against HR-defined job requirements.

## Features

- PDF and DOCX resume upload (5 MB maximum).
- Text extraction with `pypdf` and `python-docx`.
- Groq LLM-based structured candidate extraction.
- Pydantic validation of AI-generated candidate profiles.
- Prompt/completion/total token usage display.
- HR job requirements form.
- Explainable skill, experience, and education matching.
- Weighted match percentage based on assessable criteria.
- Multi-candidate shortlist, ranking, search, and filtering.
- CSV export of the current candidate comparison.
- Responsive React interface.

## Stack

- Frontend: React, JavaScript, Vite, CSS
- Backend: Python, FastAPI, Pydantic
- LLM: Groq Python SDK
- Resume parsing: pypdf, python-docx
- Tests: pytest

## Requirements

- Python 3.10+
- Node.js 18+
- A Groq API key from https://console.groq.com/

## Run locally (Windows PowerShell)

### 1. Backend

Open a terminal in the project root:

```powershell
cd backend
py -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
```

Edit `backend/.env` and add your real Groq key:

```env
GROQ_API_KEY=your_actual_groq_api_key
GROQ_MODEL=openai/gpt-oss-20b
FRONTEND_URL=http://localhost:5173
```

The model name is configurable. If Groq no longer offers the configured model in your account, choose a currently available chat model in the Groq Console and update `GROQ_MODEL`.

Start the API:

```powershell
uvicorn main:app --reload
```

API: http://127.0.0.1:8000  
Interactive API docs: http://127.0.0.1:8000/docs

### 2. Frontend

Open a second terminal in the project root:

```powershell
cd frontend
npm install
Copy-Item .env.example .env
npm run dev
```

Open the local URL printed by Vite (normally http://localhost:5173).

## How to use

1. Upload a PDF or DOCX resume.
2. Click **Extract candidate profile**. The backend extracts the text and asks Groq for structured candidate information.
3. Review the extracted profile and add the candidate to the shortlist.
4. Repeat for each candidate.
5. Enter a job title, required skills, preferred skills, minimum experience, and optional education requirement.
6. Click **Compare shortlisted candidates**.
7. Search, filter, sort, and export the comparison as CSV.

The shortlist and results are held in browser memory. Refreshing the page clears them; this MVP does not permanently store resumes or candidate records.

## Matching methodology

The default weights are:
- Skills: 60% (required skills contribute 80% of this category when both required and preferred skills are supplied; preferred skills contribute 20%).
- Experience: 25%.
- Education: 15%.

The final score is normalized over criteria that can actually be assessed. Missing information is reported as **Not assessable**, rather than automatically treated as a failure. Skill aliases are handled with a small explicit mapping; this is not semantic similarity.

These scores are decision-support information only. They should not be used as an automatic hiring decision. HR must review the source resume and assess candidates fairly.

## Tests

From the backend directory with its virtual environment activated:

```powershell
python -m pytest -v
```

## Deployment notes

The frontend can be deployed to Vercel and the FastAPI backend to Render.

Backend Render settings:
- Root directory: `backend`
- Build command: `pip install -r requirements.txt`
- Start command: `uvicorn main:app --host 0.0.0.0 --port $PORT`

Backend environment variables:
- `GROQ_API_KEY`
- `GROQ_MODEL` (optional; defaults to `openai/gpt-oss-20b`)
- `FRONTEND_URL` (the deployed frontend origin)

Frontend Vercel settings:
- Root directory: `frontend`
- Build command: `npm run build`
- Output directory: `dist`
- Environment variable: `VITE_API_BASE_URL=https://YOUR-BACKEND.onrender.com`

After deployment, set `FRONTEND_URL` on Render to the exact Vercel origin and redeploy. Never put the Groq API key in a frontend variable or commit a real `.env` file.

## Limitations

- Scanned/image-only PDFs are not OCR processed.
- PDF text extraction quality depends on the source PDF.
- The LLM can make extraction mistakes; review extracted details against the original resume.
- This MVP does not provide authentication, a database, permanent file storage, or OCR.
- The API sends extracted resume text to Groq for analysis. Do not upload resumes unless you have appropriate permission and have considered applicable privacy requirements.
