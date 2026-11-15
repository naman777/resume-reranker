"""Extract readable text from supported uploads, with bounded file sizes."""

import io
import zipfile
from pathlib import Path

from docx import Document
from fastapi import UploadFile
from pypdf import PdfReader

MAX_FILE_BYTES = 5 * 1024 * 1024
MAX_PDF_PAGES = 50
MAX_EXPANDED_DOCX_BYTES = 20 * 1024 * 1024
MAX_TEXT_CHARACTERS = 100_000
MIN_TEXT_CHARACTERS = 30


def extract_pdf(data: bytes) -> str:
    reader = PdfReader(io.BytesIO(data))
    if len(reader.pages) > MAX_PDF_PAGES:
        raise ValueError('PDF exceeds 50 pages')
    return '\n'.join(page.extract_text() or '' for page in reader.pages)


def extract_docx(data: bytes) -> str:
    with zipfile.ZipFile(io.BytesIO(data)) as archive:
        expanded_size = sum(entry.file_size for entry in archive.infolist())
        if expanded_size > MAX_EXPANDED_DOCX_BYTES:
            raise ValueError('Expanded DOCX exceeds 20 MB')

    document = Document(io.BytesIO(data))
    paragraphs = [paragraph.text for paragraph in document.paragraphs]
    table_rows = [
        ' '.join(cell.text for cell in row.cells) for table in document.tables for row in table.rows
    ]
    return '\n'.join(paragraphs + table_rows)


async def parse_upload(file: UploadFile) -> str:
    """Reject unsupported/textless files; return at most 100,000 characters."""
    data = await file.read(MAX_FILE_BYTES + 1)
    if len(data) > MAX_FILE_BYTES:
        raise ValueError('File exceeds 5 MB limit')

    extension = Path(file.filename or '').suffix.lower()
    if extension == '.pdf':
        content = extract_pdf(data)
    elif extension == '.docx':
        content = extract_docx(data)
    elif extension == '.txt':
        content = data.decode('utf-8')
    else:
        raise ValueError('Use PDF, DOCX or TXT files')

    if len(content.strip()) < MIN_TEXT_CHARACTERS:
        raise ValueError('No readable text. Scanned PDFs need OCR before upload.')

    return content[:MAX_TEXT_CHARACTERS]
