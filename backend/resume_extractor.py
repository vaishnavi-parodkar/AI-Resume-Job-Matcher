from io import BytesIO
from pathlib import Path

from docx import Document
from pypdf import PdfReader


MAX_FILE_SIZE = 5 * 1024 * 1024


def extract_resume_text(file_bytes: bytes, filename: str) -> str:
    suffix = Path(filename).suffix.lower()

    if suffix not in {".pdf", ".docx"}:
        raise ValueError("Only PDF and DOCX files are supported.")

    if not file_bytes:
        raise ValueError("The uploaded file is empty.")

    if len(file_bytes) > MAX_FILE_SIZE:
        raise ValueError("File size must not exceed 5 MB.")

    if suffix == ".pdf":
        if not file_bytes.startswith(b"%PDF-"):
            raise ValueError("The uploaded file does not appear to be a valid PDF.")
        reader = PdfReader(BytesIO(file_bytes))
        text = "\n".join(page.extract_text() or "" for page in reader.pages)

    else:
        if not file_bytes.startswith(b"PK"):
            raise ValueError("The uploaded file does not appear to be a valid DOCX file.")
        document = Document(BytesIO(file_bytes))
        paragraphs = [paragraph.text for paragraph in document.paragraphs]
        table_text = [
            " | ".join(cell.text for cell in row.cells)
            for table in document.tables
            for row in table.rows
        ]
        text = "\n".join(paragraphs + table_text)

    text = text.strip()
    if not text:
        raise ValueError(
            "No readable text was found. Scanned/image-only PDFs are not supported."
        )
    return text
