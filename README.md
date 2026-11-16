# Shortlist — AI Resume Matching and Candidate Ranking

Shortlist compares a batch of resumes with a job description, ranks candidates,
and explains the skills, experience claims and semantic similarity behind each
score. It is a working prototype for the AI / Full Stack Developer assignment.

**[Live application](https://resume-reranker.namankundra.com)** ·
**[Matching algorithm and scoring methodology](docs/MATCHING.md)** ·
**[Evaluation results](evaluation/README.md)**

Use synthetic or publicly licensed resumes only. The public demo has shared saved
history and no authentication. Scores support recruiter review; they are not
calibrated probabilities or automated hiring decisions.

## What is implemented

- Paste a JD or upload PDF, DOCX or TXT; extract skills, priorities, explicit
  experience requirements and basic qualifications.
- Upload 1–50 resumes in one batch, including the required ten-resume use case.
- Extract candidate name, email, skills, qualifications and duration claims.
- Rank candidates from 0 to 100 using actual sentence embeddings, weighted skill
  coverage and applicable experience claims.
- Inspect matched/missing skills, required-skill gaps, experience comparisons,
  component contributions and supporting resume passages.
- Search the ranking, export analysis as JSON, and reopen or delete saved runs.
- Try ten varied fictional candidates without preparing files; equivalent PDF and
  DOCX samples are included in `samples/`.

## Architecture

```mermaid
flowchart LR
    UI["React / Vite browser UI"] -->|"JD and resume files"| API["FastAPI API"]
    API --> Parser["PDF / DOCX / TXT parsing"]
    Parser --> Fields["Structured fields and source evidence"]
    Fields --> Matcher["Embeddings and weighted scoring"]
    Matcher --> Store[("PostgreSQL / SQLite")]
    Store --> API
    API -->|"Ranking and explanations"| UI
```

| Layer | Technology | Responsibility |
| --- | --- | --- |
| Frontend | React 19, Vite | Upload form, ranking table, candidate analysis and saved-run controls |
| Backend | Python, FastAPI | Validate multipart requests, coordinate parsing/scoring, expose API endpoints |
| Document parsing | pypdf, python-docx | Extract readable text from supported files |
| Structured extraction | Python rules and an alias taxonomy | Recognize fields, requirements, experience claims and evidence |
| Semantic matching | Sentence Transformers, `all-MiniLM-L6-v2`, NumPy | Encode text chunks and calculate cosine similarity |
| Persistence | SQLAlchemy, psycopg | Store completed runs in Neon PostgreSQL; SQLite is the local fallback |
| Deployment | Docker, Caddy | Serve the built frontend and API together with HTTPS |

### Request lifecycle

1. React submits the JD and resumes to `POST /api/match`. An uploaded JD takes
   precedence over pasted text.
2. FastAPI validates the batch and extracts file text. Individual unreadable
   resumes are reported while the valid ones continue.
3. The matching pipeline interprets the JD, encodes text, extracts candidate
   information, calculates component scores and sorts the candidates.
4. CPU model inference runs in a worker thread so it does not execute directly
   on the async request loop. The encoder is cached once per process.
5. The API saves the structured result and returns the ranking. The candidate
   panel shows the component breakdown and supporting text snippets.

The deployed app uses one Docker container: FastAPI serves `frontend/dist` and
`/api/*` from the same origin. Caddy terminates HTTPS and proxies to that container.
In development, Vite serves the UI separately and proxies `/api` to FastAPI.

### Database and retained data

The `runs` table stores a UUID, UTC creation timestamp and a JSON payload in a text
column. The payload contains extracted requirements, candidate details, evidence,
scores and file errors. This simple schema supports both PostgreSQL and SQLite;
it is not a normalized candidate-tracking database. The table is created on startup.

Raw uploaded resume files are processed in memory and are not archived as documents.
Extracted names, emails and supporting passages **are retained** in saved results.
All demo visitors share the same history. Old runs retain their original scores;
changing the algorithm does not silently recalculate them.

## Local setup

Run commands from the repository root. The supported reference environment is
**Python 3.12** and **Node.js 22.13+ (22.x) or Node.js 24.x**, with npm and Git.
Docker and a GPU are not required for local development. The initial model download
requires internet access; no paid API key is needed.

### 1. Clone the repository

```bash
git clone https://github.com/naman777/resume-reranker.git
cd resume-reranker
```

The repository is private, so the cloning account needs access.

### 2. Install the backend

Windows PowerShell (explicit virtual-environment paths avoid activation-policy issues):

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install torch --index-url https://download.pytorch.org/whl/cpu
.\.venv\Scripts\python.exe -m pip install -r backend/requirements.txt
.\.venv\Scripts\python.exe -c "from backend.semantic import model; model()"
```

macOS/Linux:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install torch --index-url https://download.pytorch.org/whl/cpu
.venv/bin/python -m pip install -r backend/requirements.txt
.venv/bin/python -c "from backend.semantic import model; model()"
```

Install CPU Torch first to avoid unnecessary GPU dependencies. The last command
prefetches the embedding model; later runs reuse the Hugging Face cache.
`backend/requirements.lock.txt` is the captured dependency snapshot for reproducing
that environment; install it instead of `requirements.txt` after installing CPU
Torch if you need the pinned versions.

### 3. Choose a database

**SQLite:** no database configuration is needed for a fresh local checkout.
Without `DATABASE_URL`, the backend creates `rankings.db` in the working directory.

**Neon/PostgreSQL:** copy `backend/.env.example` to `backend/.env` and replace its
placeholder with a valid connection string:

```dotenv
DATABASE_URL=postgresql://USER:PASSWORD@HOST/DATABASE?sslmode=require
```

Keep the connection parameters supplied by Neon. Standard `postgres://`,
`postgresql://` and `postgresql+psycopg://` URLs are accepted; the first two are
normalized to the installed psycopg driver. Never put the database URL in frontend
configuration. Environment files are ignored by Git.

The backend loads process variables first, then `backend/.env`, then the root
`.env`, without overwriting an already configured value. Restart after changing
settings. `APP_ENV=production` requires an explicit database URL. Switching from
SQLite to PostgreSQL does not migrate old history automatically.

The optional root `compose.yaml` starts **only a local PostgreSQL database**:
`docker compose up -d db`. For that database, use
`postgresql+psycopg://shortlist:local-dev-only@127.0.0.1:5432/shortlist` locally.
It is separate from the full-app deployment configuration.

### 4. Build the frontend

These commands work from the root in PowerShell and POSIX shells:

```bash
npm --prefix frontend ci
npm --prefix frontend run build
```

### 5. Start the application

Windows PowerShell:

```powershell
.\.venv\Scripts\python.exe -m uvicorn backend.main:app --host 127.0.0.1 --port 8000
```

macOS/Linux:

```bash
.venv/bin/python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000
```

Open **http://localhost:8000**. Interactive API documentation is at
**http://localhost:8000/docs**. Build the frontend before starting FastAPI; if it
was started before `frontend/dist` existed, restart it after the first build.

For frontend hot reload, leave FastAPI running and use another terminal:

```bash
npm --prefix frontend run dev
```

Open **http://localhost:5173**. The Vite proxy forwards API calls to port 8000.

### Configuration reference

| Variable | Default | Purpose |
| --- | --- | --- |
| `DATABASE_URL` | `sqlite:///./rankings.db` locally | Database connection; required explicitly in production |
| `EMBEDDING_MODEL` | `sentence-transformers/all-MiniLM-L6-v2` | Encoder identifier |
| `APP_ENV` | Unset | `production` enables the explicit-database guard |
| `PRELOAD_MODEL` | Unset | `1` loads the encoder before startup completes |
| `HF_HOME` | Library cache location | Hugging Face cache directory |
| `HF_HUB_OFFLINE` | Library default | `1` uses cached model files without Hub access |
| `TRANSFORMERS_OFFLINE` | Library default | Offline loading used in the Docker image |

The production image includes the default model and enables offline loading.
Changing its model requires building an image containing the corresponding weights.
Host-specific Docker, Caddy, health-check and restart instructions are in
**[docs/DEPLOYMENT.md](docs/DEPLOYMENT.md)**.

## Matching algorithm and score calculation

The default formula, when all components are active, is:

```text
Overall score ≈ 100 × (0.45 × semantic_similarity
                     + 0.40 × weighted_skill_coverage
                     + 0.15 × experience_fit)
```

| Component | Calculation | Weight |
| --- | --- | ---: |
| Semantic | Average best resume-chunk cosine match for each JD chunk, clamped to [0,1] | 45% |
| Skills | Matched JD skill weights divided by all recognized JD skill weights | 40% |
| Experience | Applicable explicit years divided by required years, capped at 1 | 15% |

Required/default skills have coverage weight 1; desirable skills have weight 0.25.
Applicable skill-specific experience is preferred over general tenure. General
claims are marked as unverified for role relevance. Missing candidate evidence
scores zero where a requirement exists; missing JD requirements cause the relevant
component to be omitted and the remaining weights normalized.

For example, with required Python and React, desirable Docker, and three required
years: matching Python and React gives `2/2.25` skill coverage. With two applicable
years and an illustrative semantic score of 80%, the contributions are 36.00,
35.56 and 10.00 points, producing **81.6/100** after rounding.

Each component contribution is rounded to two decimal places; their sum is rounded
to one decimal. Candidates are ordered by final score, then candidate name for ties.
Missing required skills are displayed but do not automatically disqualify someone.
Qualifications are extracted and displayed, not scored separately.

**[The full methodology](docs/MATCHING.md)** explains chunking, aliases, experience
selection, weight normalization, rounding, the worked example and known limitations.
The model is pretrained and used for inference; no LLM prompt or generated score
is substituted for the calculation.

## API overview

| Method | Endpoint | Purpose |
| --- | --- | --- |
| GET | `/api/health` | Basic liveness and configured model identifier |
| POST | `/api/match` | Multipart fields: `jd`, repeated `resumes`, optional `jd_file` |
| GET | `/api/runs` | List the latest twenty saved-run IDs and timestamps |
| GET | `/api/runs/{id}` | Retrieve a complete saved result |
| DELETE | `/api/runs/{id}` | Delete a saved result |

Each file is limited to **5 MiB**, PDFs to **50 pages**, expanded DOCX contents to
**20 MiB**, and extracted text to **100,000 characters**. Files need at least thirty
characters after trimming leading/trailing whitespace. The batch must contain 1–50 resumes.
Uploaded JD files replace pasted text. Pasted JDs must be 30–100,000 characters.

Invalid batches/JDs or batches with no readable resumes return HTTP 400. Missing
required multipart fields can return FastAPI's HTTP 422. A matching failure returns
HTTP 503; valid files can still succeed alongside individual parsing errors.
A missing saved run returns HTTP 404 on retrieval. Use `/docs` to inspect the exact
request schema and try uploads.

## Repository structure

```text
backend/                 FastAPI, parsers, extraction, semantic matching and storage
frontend/src/
  components/            Form, ranking, evidence and candidate-analysis components
  hooks/                 Workspace state and asynchronous actions
  api/                   HTTP requests and error handling
  data/                  Synthetic demo profiles
  styles/                Readable styles grouped by purpose
docs/                    Matching explanation and deployment guide
tests/                   Backend, parser and evaluation regression tests
samples/                 Ten fictional PDF/DOCX resumes and extraction evaluation
evaluation/              Frozen ranking challenge, baselines and generated reports
deploy/                  Production Compose, Caddy example and public smoke check
.github/workflows/       Automated quality checks and manual real-model benchmark
```

The main scoring files are `semantic.py` (embeddings), `skills.py`/`taxonomy.py`
(skill recognition), `experience.py` (claims), `requirements.py` (JD priorities),
`scoring.py` (formulas) and `matching.py` (candidate results and ordering).

## Tests and evaluation

Install development dependencies into the same virtual environment:

```powershell
# Windows PowerShell
.\.venv\Scripts\python.exe -m pip install -r backend/requirements-dev.txt
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m ruff check backend tests samples deploy evaluation
.\.venv\Scripts\python.exe -m ruff format --check backend tests samples deploy evaluation
```

```bash
# macOS/Linux
.venv/bin/python -m pip install -r backend/requirements-dev.txt
.venv/bin/python -m pytest -q
.venv/bin/python -m ruff check backend tests samples deploy evaluation
.venv/bin/python -m ruff format --check backend tests samples deploy evaluation
```

```bash
npm --prefix frontend run lint
npm --prefix frontend run format:check
npm --prefix frontend test
npm --prefix frontend run build
```

The current suite has **44 backend tests and 5 frontend tests**. Backend API tests
use temporary SQLite databases and stub embedding inference; they do not write to
Neon. Frontend tests use mock API responses. These checks do not replace real-model
or public-deployment verification.

Run the following Python modules with the same virtual-environment interpreter
(`.\.venv\Scripts\python.exe` on Windows or `.venv/bin/python` on macOS/Linux):

| Command after the interpreter | What it verifies |
| --- | --- |
| `-m tests.smoke_real` | Ten distinct mixed PDF/DOCX resumes using actual embeddings; deletes its own saved test run |
| `-m samples.evaluate` | Expected fields for ten fictional candidates in text, PDF and DOCX |
| `-m evaluation.run` | All thirty challenge resumes against three JDs using three ranking methods |
| `-m evaluation.run --lexical-only` | Model-free baseline comparison, with separate output files |
| `-m evaluation.review` | Blind worksheet without assistant labels or model scores for human review |
| `deploy/verify.py` | Public HTTPS, assets, matching, explanations, parsing errors and saved-run persistence |

`tests.smoke_real` and `deploy/verify.py` exercise the configured application/database
and delete only their own synthetic run. The offline ranking benchmark never saves
application runs. Regenerate optional sample documents with `samples/generate.py`;
ReportLab is included in development dependencies.

On the frozen synthetic ranking challenge, macro nDCG@5 is **0.626** for skill
coverage, **0.928** for the TF-IDF hybrid and **0.932** for the embedding hybrid.
Both hybrids have Precision@5 of 0.800, and embedding pairwise agreement is slightly
lower. These are assistant-authored labels, not independently human-validated
accuracy percentages. The report includes failures and was reproduced in the Linux
production image and GitHub Actions.

Read **[the evaluation methodology](evaluation/README.md)** and
**[the generated report](evaluation/results/benchmark.md)**. CI runs lint, formatting,
tests, frontend builds and the model-free benchmark on pushes and pull requests.
A separate manually triggered workflow runs real embeddings and uploads reports.

## Demo walkthrough

1. Open the app and click **Try 10 sample candidates**, then **Match candidates**.
2. Explain the required/desirable skills and the three-year experience minimum.
3. Compare a strong full-stack profile with the Java-focused profile.
4. Open Candidate 03: show eight reported years but two applicable Python years.
5. Expand a supporting skill passage and explain the weighted contributions.
6. Upload the provided PDF/DOCX files, then demonstrate an individual bad-file error.
7. Export the analysis and reopen the saved result.

A recorded submission video remains a separate deliverable.

## Known limitations and troubleshooting

Names, qualifications, negation and JD priorities use heuristics. The taxonomy is
finite; skill-specific duration claims can support only part of a role. Dates are
not converted into a verified career timeline, alternatives such as "Python or
Java" are not modeled, and qualifications have no separate score. Scanned PDFs
require OCR. Keyword-heavy profiles can still rank too highly; semantic matching
does not establish truthful experience or fairness.

| Symptom | Check |
| --- | --- |
| Homepage returns 404 | Build `frontend/dist`, then restart FastAPI if it was missing at startup |
| Matching returns 503 | Inspect backend logs; pre-download the encoder and check model/cache availability |
| File has no readable text | Use a text-based file or perform OCR before upload |
| Wrong database/history appears | Check the working directory and configuration precedence; restart after changes |
| PostgreSQL connection fails | Check the URL, connectivity and TLS parameters supplied by the database provider |
| First match is slow | Model loading/download is deferred locally unless preloaded; production preloads it |

The application is a demonstration prototype. Shared unauthenticated history and
stored extracted details make it unsuitable for real candidate data without
additional access controls, retention policies and independent evaluation.
