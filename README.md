# Shortlist — Resume matching & candidate ranking

Prototype for the Avom assignment received November 15, 2026. Submission window: November 20–22. Use synthetic/sample or publicly licensed data only.

## Run

Python 3.12+ and Node 20+:

```bash
python -m venv .venv
source .venv/bin/activate
# CPU build avoids downloading GPU dependencies:
pip install torch --index-url https://download.pytorch.org/whl/cpu
pip install -r backend/requirements.txt
python -c "from backend.matching import model; model()"
cd frontend
npm ci
npm run build
cd ..
uvicorn backend.main:app --host 0.0.0.0 --port 8000
```

Open http://localhost:8000. API docs: http://localhost:8000/docs.
For frontend development use `npm run dev` in frontend; Vite proxies `/api` to port 8000. No API keys needed. Initial model download requires Internet; subsequent runs use the Hugging Face cache. Model errors return 503, never fake scores.

Click **Try 10 sample candidates**, then **Match candidates** for a synthetic demo. Upload PDFs/DOCX individually or in batches (up to 50). Paste a JD or upload one; uploaded JD takes precedence. Review ranking, open candidate analysis, export JSON, or revisit/delete saved runs.

## Architecture

React/Vite → multipart FastAPI endpoint → pypdf/python-docx → structured extraction → Sentence Transformers → explainable scoring → SQLAlchemy database. FastAPI serves the compiled frontend. SQLite is the zero-configuration development default; PostgreSQL is supported through `DATABASE_URL=postgresql+psycopg://user:password@localhost:5432/shortlist`. `docker compose up -d` starts a development Postgres. Set the URL before starting the API. Schema is initialized on startup.

Raw resumes are processed in memory, not stored. Results include extracted candidate details and are persisted locally. Saved runs can be deleted. This prototype has no user authentication; use locally with synthetic data. Production requires authentication, authorization, migrations, rate limits, retention rules, and independent matching evaluation.

## Matching methodology

Default overall score = **45% semantic similarity + 40% recognized skill coverage + 15% explicit experience fit**. Components are in [0,100]. Each candidate includes scores, normalized weights and exact weighted contributions; totals are rounded to one decimal.

- Semantic: `sentence-transformers/all-MiniLM-L6-v2` normalized embeddings; 180-word chunks, 40-word overlap. For each JD chunk take the best cosine similarity among resume chunks, then average and clamp to [0,1]. Chunking reduces truncation. Candidate first-line name and email are removed before embedding. Semantic score is not a probability or an objectively calibrated assessment of job performance.
- Skills: fraction of recognized JD skills present in the resume. A transparent, extensible alias dictionary uses word boundaries (Java does not match JavaScript). All detected JD skills currently have equal weight, including desirable skills. Skills outside the dictionary still affect embeddings but not skill coverage.
- Experience: `min(candidate years / JD years, 1)`. Parse explicit year claims only; missing candidate years receives zero when JD requires years. If JD experience is absent, omit its component and normalize the remaining weights. Similarly omit skill coverage if no recognized JD skills. Explicit claims are estimates, not verified relevant career timelines; overlapping employment dates are not summed. Numeric ranges currently resolve to the largest explicit value, so recruiter review is required.
- Qualifications are extracted and displayed, not independently weighted; education content may affect semantic similarity. No age, gender or contact fields are explicitly scored. Embeddings can still contain bias; no fairness claim is made.

Missing skills mean **not detected**, not proof of absence. The skill taxonomy, experience extraction, score weights, and semantic alignment need evaluation on labeled data before real recruiting use. No labeled calibration dataset is included, so accuracy is not claimed.

## Verification

```bash
.venv/bin/python -m pytest -q
cd frontend && npm run build
```

Tests cover skill boundaries, scoring contributions, missing experience, 10 DOCX batch parsing, partial file failure, persistence, and deletion. Model inference is stubbed in integration tests to keep them deterministic; run the app demo separately for real embeddings. Scanned PDFs require OCR externally; corrupt, oversized, unsupported or textless uploads receive individual errors. Each file is limited to 5 MB, PDF to 50 pages, and expanded DOCX to 20 MB.

## Demo walkthrough

1. Start server; load the ten synthetic sample candidates.
2. Explain the JD skills and experience requirements.
3. Rank candidates, compare top and lower matches, inspect missing skills.
4. Explain each weighted score in candidate analysis.
5. Upload the generated PDF/DOCX sample files, demonstrate a bad file error.
6. Export results and reopen a saved run.

Source repository: https://github.com/naman777/resume-reranker (private). A recorded demo remains a submission task; no public deployment is claimed.

Generate optional sample documents: `pip install reportlab && python samples/generate.py`. ReportLab is only a sample-generation dependency.

Real embedding verification (after generating samples): `PYTHONPATH=. .venv/bin/python tests/smoke_real.py`. This checks ten mixed PDF/DOCX documents end to end without stubbing the model. The initial implementation was checked with three deterministic tests, a production frontend build, and the real-model smoke test. Browser interaction QA was unavailable in the build environment.

`backend/requirements.lock.txt` captures the tested environment. For a repeatable CPU installation, install Torch from the CPU index first, then use this lock file instead of requirements.txt.
