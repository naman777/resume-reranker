# Shortlist — Resume matching & candidate ranking

Prototype for the Avom assignment received November 15, 2026. Submission window: November 20–22. Use synthetic/sample or publicly licensed data only.

## Run

Python 3.12+ and Node 20.19+:

```bash
python -m venv .venv
source .venv/bin/activate
# CPU build avoids downloading GPU dependencies:
pip install torch --index-url https://download.pytorch.org/whl/cpu
pip install -r backend/requirements.txt
python -c "from backend.semantic import model; model()"
cd frontend
npm ci
npm run build
cd ..
uvicorn backend.main:app --host 0.0.0.0 --port 8000
```

Open http://localhost:8000. API docs: http://localhost:8000/docs.
For frontend development use `npm run dev` in frontend; Vite proxies `/api` to port 8000. No API keys needed. Initial model download requires Internet; subsequent runs use the Hugging Face cache. Model errors return 503, never fake scores.

Click **Try 10 sample candidates**, then **Match candidates** for a synthetic demo. Upload PDFs/DOCX individually or in batches (up to 50). Paste a JD or upload one; uploaded JD takes precedence. Review ranking, open candidate analysis, export JSON, or revisit/delete saved runs.

## Deployment on operator-prod

Live application: https://resume-reranker.namankundra.com

The full application runs in one Docker container: FastAPI serves the compiled
React frontend and the API. The CPU embedding model is downloaded into the image
at build time, loaded before startup completes, and used offline at runtime.

The deployment directory on the host is `/opt/resume-reranker`. Runtime secrets
are in `deploy/.env` with mode `600`, outside the image. Set `DATABASE_URL` to the
Neon URL; production startup fails if it is missing.

```bash
cd /opt/resume-reranker
sudo docker compose -f deploy/compose.yaml up -d --build
sudo docker compose -f deploy/compose.yaml ps
sudo docker compose -f deploy/compose.yaml logs --tail=50 app
curl --fail http://127.0.0.1:8011/api/health
```

`deploy/compose.yaml` joins the existing `foreman-production_default` proxy network
and exposes port 8011 on loopback only. The existing Caddy container proxies
`resume-reranker.namankundra.com` to `resume-reranker:8000` and manages HTTPS.
The site block is in `deploy/Caddyfile`; merge it into the host Caddyfile, validate
the combined configuration, then reload Caddy. DNS must point the subdomain to
the host. Other applications on the proxy keep their existing routes.

The current proxy container has an older file bind mount. To reload the current
host configuration without restarting other sites, copy it into the container
and validate that copy before reloading:

```bash
sudo docker cp /home/nkundra_be23/Foreman/deploy/Caddyfile foreman-production-caddy-1:/tmp/Caddyfile.reload
sudo docker exec foreman-production-caddy-1 caddy validate --config /tmp/Caddyfile.reload --adapter caddyfile
sudo docker exec foreman-production-caddy-1 caddy reload --config /tmp/Caddyfile.reload --adapter caddyfile
```

The container runs as an unprivileged user, has a 1.5 GB memory limit and 1.5 CPU
limit, restarts automatically, and checks health every 30 seconds. Model startup
has a two-minute health-check grace period. Use synthetic data for this public
assignment demo; all visitors share the same saved-run history.

Run `python deploy/verify.py` from a checkout to verify HTTPS, frontend assets,
ten mixed PDF/DOCX uploads with real embeddings, explanation fields, partial-file
failure and database persistence. It deletes only its own synthetic test run.
The production image also passed all 36 backend tests on Linux. Installed Python
versions are recorded on the server in `deploy/requirements.installed.txt`.

## Architecture

React/Vite → multipart FastAPI endpoint → pypdf/python-docx → structured extraction → Sentence Transformers → explainable scoring → SQLAlchemy database. FastAPI serves the compiled frontend.

### Database configuration

Put your Neon connection string in `backend/.env` as `DATABASE_URL` (see
`backend/.env.example`). The backend loads this file automatically, followed by
the repository-root `.env`. Variables already set in the process take precedence.
Restart the backend after changing a connection string.

Standard `postgresql://`, `postgres://` and `postgresql+psycopg://` URLs are
supported through the psycopg driver. Keep the TLS query parameters supplied by
Neon, including `sslmode=require`. Connections are checked before reuse and
recycled after five minutes. The `runs` table is created on application startup.
Connection strings stay on the backend; `.env` files are excluded from Git.

When no `DATABASE_URL` is configured, SQLite remains the local development fallback.
`docker compose up -d` is an alternative for running PostgreSQL locally. Changing
databases does not automatically migrate previous SQLite history.

Raw resumes are processed in memory, not stored. Results include extracted candidate details and supporting text snippets, and are persisted in the configured database. Saved runs can be deleted. This prototype has no user authentication; use locally with synthetic data. Production requires authentication, authorization, migrations, rate limits, retention rules, and independent matching evaluation.

## Code organization and development checks

The frontend entry point only mounts `App`. `App` composes the workspace, while
`useMatchingWorkspace` owns form state, matching requests and saved-run actions.
Components receive data and callbacks; they do not fetch API data themselves.

```text
frontend/src/
  main.jsx                    React entry point
  App.jsx                     Workspace composition
  components/                 Inputs, uploads, rankings, analysis and layout
  hooks/useMatchingWorkspace.js  Workspace state and async actions
  api/rankings.js             HTTP requests and response error handling
  data/samples.js             Synthetic demo data
  utils/exportRanking.js     JSON download
  styles/                    Base, layout, forms, results and responsive CSS

backend/
  config.py                  Environment loading and database URL configuration
  main.py                    FastAPI setup and frontend mounting
  routes.py                  HTTP validation and request coordination
  parsing.py                 PDF/DOCX/TXT text extraction and upload limits
  extraction.py              Candidate identity and structured information
  taxonomy.py                Skill aliases and qualification patterns
  skills.py                  Skill detection, negation and supporting evidence
  experience.py              Duration claims and role relevance comparison
  requirements.py            Required/desirable JD requirements
  evidence.py                Source snippets and extracted-text line numbers
  semantic.py                Cached model, text chunks and embedding similarity
  matching.py                Weighted scoring, explanations and ranking
  scoring.py                 Component formulas and versioned weights
  database.py                Saved-run persistence
```

Install Python development tools with `pip install -r backend/requirements-dev.txt`.
From the repository root, run:

```bash
python -m ruff check backend tests samples
python -m ruff format --check backend tests samples
python -m pytest -q
```

From `frontend`, run:

```bash
npm ci
npm run lint
npm run format:check
npm test
npm run build
```

Use `npm run format` for frontend formatting and `python -m ruff format backend tests samples`
for Python formatting. Frontend regression tests simulate matching ten samples,
candidate analysis, search, failed requests and saved-run restore/deletion with
mock API responses. They do not run the embedding model or replace a browser demo.
Backend API regression tests use a temporary SQLite database so they do not write
to the configured Neon database.

## Matching methodology

Default overall score = **45% semantic similarity + 40% recognized skill coverage + 15% explicit experience fit**. Components are in [0,100]. Each candidate includes scores, normalized weights and exact weighted contributions; totals are rounded to one decimal.

- Semantic: `sentence-transformers/all-MiniLM-L6-v2` normalized embeddings; 180-word chunks, 40-word overlap. For each JD chunk take the best cosine similarity among resume chunks, then average and clamp to [0,1]. Chunking reduces truncation. Detected name lines and emails are removed before embedding. Semantic score is not a probability or an objectively calibrated assessment of job performance.
- Skills: weighted recognized skill coverage. Required/default skills receive weight 1; explicitly desirable skills receive weight 0.25. For a JD requiring Python with optional Docker, Python alone gives 80% skill coverage; Docker alone gives 20%. This is the skills component, not the overall score. Headings and cues such as "must have", "preferred" and "nice to have" determine priority; a required mention wins over a desirable mention. Aliases use word boundaries (Java does not match JavaScript), and common explicit negations such as "no Python experience" do not count as skill evidence. Skills outside the dictionary still affect embeddings but not coverage.
- Experience: `min(applicable candidate years / required JD years, 1)`. Ranges such as 3–5 years use their lower bound, and months are converted to years. Explicit skill-specific experience takes precedence over general tenure; unrelated skill-specific claims are not credited. For example, 8 years total and 2 years Python compares as 2 years against a Python role. General claims are a fallback and explicitly marked as unverified for role relevance. Common education/course durations are excluded. Missing applicable years scores zero when the JD requires experience. If no JD experience is detected, omit this component and normalize the remaining weights; similarly omit skill coverage when no JD skills are recognized.
- Qualifications are extracted and displayed, not independently weighted; education content may affect semantic similarity. No age, gender or contact fields are explicitly scored. Embeddings can still contain bias; no fairness claim is made.

Each matched skill and experience claim includes a verbatim snippet and its line number in extracted text (not a PDF page coordinate). New saved runs carry scoring version `2.0`; old runs retain their original scores and remain viewable without the new evidence fields.

Missing skills mean **not detected**, not proof of absence. Name detection, priority cues and negation are heuristics. Work dates are not reconstructed or summed; explicit claims are unverified. A skill-specific claim can support only part of a role. Where a JD contains several distinct experience thresholds, this prototype uses the strongest detected general minimum (or strongest scoped minimum when no general claim exists), rather than evaluating a separate threshold per skill. Alternative requirements such as "Python or Java" are not modeled as alternatives. The taxonomy, weights and semantic alignment still need independent evaluation; scores are not calibrated hiring probabilities.

## Verification

### Ranking challenge and baselines

The project now includes a frozen challenge set of three JDs and thirty new
synthetic resumes (ninety relevance judgments), separate from the demo fixtures.
Compare weighted skill coverage, a TF-IDF hybrid and the actual embedding hybrid:

```bash
python -m evaluation.run
python -m evaluation.run --lexical-only
python -m evaluation.review
```

The measured macro nDCG@5 values are **0.626 / 0.928 / 0.932**, respectively.
The two hybrids both have Precision@5 of 0.800; embeddings have slightly lower
pairwise agreement than TF-IDF. This is a small synthetic set with assistant-authored
labels, not independent human validation or a hiring-accuracy percentage.

See [the evaluation methodology and failure analysis](evaluation/README.md) and
[the complete generated report](evaluation/results/benchmark.md). The blind review
export deliberately omits labels and scores so a person can provide an independent
review. No matcher weights or extraction rules were tuned on these challenge results.

[Quality checks](.github/workflows/ci.yml) run Python/JavaScript lint, formatting,
tests, the frontend build and a model-free benchmark on pushes and pull requests.
[The real-model workflow](.github/workflows/benchmark.yml) can be started manually
and uploads the full comparison report. Neither workflow needs database credentials.

### Application regression checks

```bash
.venv/bin/python -m pytest -q
cd frontend && npm run build
```

Tests cover skill boundaries, scoring contributions, missing experience, 10 DOCX batch parsing, partial file failure, persistence, and deletion. Model inference is stubbed in integration tests to keep them deterministic; run the app demo separately for real embeddings. Scanned PDFs require OCR externally; corrupt, oversized, unsupported or textless uploads receive individual errors. Each file is limited to 5 MB, PDF to 50 pages, and expanded DOCX to 20 MB.

### Synthetic extraction evaluation

The shared fixtures in `frontend/src/data/candidates.json` include headings before
names, contact-first resumes, month-based claims, ranges, freshers with course
durations, total versus skill-specific experience, negated skills, employment dates
without explicit year counts, and a DOCX table. The demo button uses these same ten
fictional profiles. Regenerate their document versions and evaluate from the root:

```bash
python samples/generate.py
python -m samples.evaluate
```

For each format (text, PDF and DOCX), the current extraction matches all ten expected
values in each field. Comparison with the original committed extractor on the same
fixtures gives:

| Field | Original correct / 10 | Current correct / 10 |
| --- | ---: | ---: |
| Candidate name | 1 | 10 |
| Explicit experience | 7 | 10 |
| Recognized skill set | 9 | 10 |
| Qualifications | 10 | 10 |

These are regression results on a small, authored synthetic set, not independent
accuracy measurements or evidence of generalization to real resumes.

## Demo walkthrough

1. Start server; load the ten synthetic sample candidates.
2. Explain the required versus desirable JD skills and the experience requirement.
3. Rank candidates; compare Candidate 01 with the Java-focused Candidate 06.
4. Open Candidate 03: show 8 years total versus 2 years Python used in scoring.
5. Expand a skill's supporting passage and explain each weighted score.
6. Upload the generated PDF/DOCX sample files, demonstrate a bad file error.
7. Export results and reopen a saved run.

Source repository: https://github.com/naman777/resume-reranker (private). Live demo:
https://resume-reranker.namankundra.com. A recorded submission video remains a separate task.

Generate optional sample documents: `pip install reportlab && python samples/generate.py`. ReportLab is only a sample-generation dependency.

Real embedding verification (after generating samples): `python -m tests.smoke_real`.
This checks ten distinct candidates in mixed PDF/DOCX formats end to end with actual
embeddings, validates the strong-versus-unrelated ranking, checks experience
selection, and deletes its synthetic saved run. The real-model check passed with
scores ranging from 27.2 to 77.5 on the current fixtures. Live browser QA also
verified the ten-profile demo, required/desirable skill display, reported versus
scored experience, expanded evidence snippets and restoring the saved run from
Neon after reloading. A recorded submission video remains a separate deliverable.

`backend/requirements.lock.txt` captures the tested environment. For a repeatable CPU installation, install Torch from the CPU index first, then use this lock file instead of requirements.txt.
