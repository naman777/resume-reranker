"""Generate varied, entirely fictional PDF and DOCX resumes for the demo."""

import json
from pathlib import Path
from textwrap import wrap

from docx import Document
from reportlab.pdfgen import canvas

ROOT = Path(__file__).resolve().parent
FIXTURES = ROOT.parent / 'frontend/src/data/candidates.json'


def write_docx(path: Path, text: str, use_table: bool) -> None:
    document = Document()
    for line in text.splitlines():
        if use_table and ' | ' in line:
            cells = document.add_table(rows=1, cols=2).rows[0].cells
            cells[0].text, cells[1].text = line.split(' | ', 1)
        else:
            document.add_paragraph(line)
    document.save(path)


def write_pdf(path: Path, text: str) -> None:
    pdf = canvas.Canvas(str(path))
    pdf.setFont('Helvetica', 11)
    y = 790
    for line in text.splitlines():
        for wrapped in wrap(line, width=85) or ['']:
            pdf.drawString(50, y, wrapped)
            y -= 18
        y -= 6
    pdf.save()


def generate_samples() -> None:
    for index, fixture in enumerate(json.loads(FIXTURES.read_text()), start=1):
        write_docx(ROOT / f'{fixture["id"]}.docx', fixture['text'], use_table=index == 7)
        write_pdf(ROOT / f'{fixture["id"]}.pdf', fixture['text'])
    print('Generated 10 fictional candidates in both PDF and DOCX formats.')


if __name__ == '__main__':
    generate_samples()
