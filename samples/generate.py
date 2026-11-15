"""Generate ten entirely fictional DOCX and PDF resumes; no personal data."""
from pathlib import Path
from docx import Document
from reportlab.pdfgen import canvas
ROOT = Path(__file__).parent
for i in range(10):
    lines = [f'Synthetic Candidate {i+1:02d}', f'sample{i+1}@example.com', f'{i%6+1} years of experience', 'Bachelor of computer science', ['Python FastAPI React PostgreSQL REST APIs Docker Git automated testing NLP', 'Java Spring Boot SQL Docker Git', 'JavaScript React HTML CSS'][i%3], 'Built web applications, backend services and accessible user interfaces.']
    doc = Document()
    for line in lines: doc.add_paragraph(line)
    doc.save(ROOT / f'candidate-{i+1:02d}.docx')
    pdf = canvas.Canvas(str(ROOT / f'candidate-{i+1:02d}.pdf'))
    for j, line in enumerate(lines): pdf.drawString(50, 790-j*24, line)
    pdf.save()
