# Matching algorithm and scoring methodology

Shortlist compares a job description (JD) with each resume using three signals:
semantic text similarity, recognized skill coverage, and explicit experience fit.
It returns a score from 0 to 100, an ordered shortlist, and an explanation of the
components. The current scoring version is **2.0**.

The score measures alignment with the supplied JD. It is not a probability of
job performance, an eligibility decision, or a calibrated hiring recommendation.
The pretrained embedding model is used for inference; it is not fine-tuned here.

## 1. Extract text and structured information

The API accepts pasted JD text or an uploaded JD. An uploaded JD takes precedence.
Resumes are uploaded together in a multipart request.

| Input | Extraction |
| --- | --- |
| Text-based PDF | `pypdf` extracts text from each page |
| DOCX | `python-docx` reads paragraphs, then table rows |
| TXT | UTF-8 decoding |

Each file is limited to 5 MiB; PDFs are limited to 50 pages, and expanded DOCX
contents to 20 MiB. Extracted text is capped at 100,000 characters. Textless scans
need external OCR. A corrupt resume produces an individual error while valid
files continue. If no resume is readable, the request is rejected.

Rule-based extraction identifies a candidate name, email, recognized skills,
basic qualifications, explicit duration claims, and supporting passages. Labeled
names are preferred; otherwise the parser examines early non-heading lines and
falls back to the filename. Complex layouts can still confuse these heuristics.

The skill taxonomy maps aliases to canonical names, for example `reactjs` to
`React`, `k8s` to `Kubernetes`, and `pytest` to `Testing`. Word boundaries prevent
`Java` from matching `JavaScript`. Common local negations, such as "no Python
experience", are excluded, but this is not a complete natural-language negation
parser. Related labels can overlap: `PostgreSQL` also contributes to recognized
`SQL` under the current taxonomy.

## 2. Interpret JD requirements

Recognized skills default to required. Headings and cues such as "required",
"must have", "preferred", "optional" and "nice to have" determine priority.
A required occurrence wins if the same skill appears in both groups.

Each recognized JD skill receives a coverage weight:

| Priority | Skill weight |
| --- | ---: |
| Required/default | 1.00 |
| Desirable | 0.25 |

Experience requirements are extracted from required passages. A range such as
"3–5 years" uses its lower bound, 3. When several general minimums are detected,
the strongest is used. If no general claim exists, the strongest scoped minimum
is used. The system does not evaluate a separate minimum for every skill, nor
does it model alternatives such as "Python or Java" as interchangeable options.

Qualifications are displayed but do not have a separate scoring component.
Education wording may still influence semantic similarity.

## 3. Calculate semantic similarity

The default encoder is `sentence-transformers/all-MiniLM-L6-v2`, running on CPU.
The model is loaded lazily and cached once per process. Production preloads the
model before accepting requests and includes its cached weights in the image.

Detected name lines and email addresses are removed from resume text before
embedding. The JD and each resume are split into 180-word chunks with 40-word
overlap (a stride of 140 words). This reduces whole-document truncation, although
word-based chunks can still exceed the tokenizer's token limit.

The encoder produces normalized vectors. Their dot product is cosine similarity.
For each JD chunk, find the best-matching resume chunk; average those best matches
and clamp the result to the range zero through one:

```text
q_i = normalized embedding of JD chunk i
r_j = normalized embedding of resume chunk j

S = clip(mean_i(max_j(dot(q_i, r_j))), 0, 1)
Semantic component percentage = 100 × S
```

This captures some related wording without requiring identical keywords. It does
not prove that a claim is true. The same resume chunk can support several JD
chunks, and keyword-heavy or unrelated text can still receive similarity credit.

## 4. Calculate weighted skill coverage

Matched skills are the intersection of recognized JD and resume skill sets.
Missing skills are recognized JD skills not detected in the resume. Each skill
counts once, regardless of how often it appears.

```text
K = sum(weight of each matched JD skill) / sum(weight of all recognized JD skills)
Skills component percentage = 100 × K
```

For required Python and React plus desirable Docker, the denominator is
`1 + 1 + 0.25 = 2.25`. Matching Python and React gives `2 / 2.25 = 0.888889`,
or **88.89% skill coverage**. This is one component, not the overall score.

A missing required skill reduces coverage but does not automatically disqualify
the candidate or impose an overall score cap. Skills outside the taxonomy can
affect embeddings but do not enter this explicit coverage calculation. "Missing"
means not detected; it is not proof that a candidate lacks the skill.

## 5. Select applicable experience and calculate fit

The parser recognizes explicit years and months, including `3+ years`, `3–5 years`
and `18 months`. Ranges use the lower bound; months are converted to years.
Common degree/course durations and negated claims are excluded. Employment dates
are not reconstructed, and durations from different jobs are not added together.

The reported experience shown in the dashboard prefers a general/total claim;
otherwise it uses the largest detected scoped duration. Experience used for
scoring is selected separately:

1. Prefer explicit claims mentioning at least one recognized required JD skill.
2. If none exist, use general experience claims and mark role relevance unverified.
3. If the JD has no required skills, scoped claims can serve as a general fallback.
4. Otherwise, unrelated scoped tenure is not credited.

The largest applicable claim is used, not the sum. A claim connected to one
required skill does not establish experience across the whole role.

```text
A = applicable candidate years
R = positive JD minimum years

E = min(A / R, 1)
Experience component percentage = 100 × E
```

If a positive JD minimum exists but no applicable candidate claim is found,
`E = 0`. Extra years above the minimum do not earn more than 100% in this component.
If no positive JD minimum is detected, the component is omitted.

For a Python role requiring three years, a resume claiming "8 years total" and
"2 years using Python" uses **2**, not 8: `E = 2 / 3 = 0.666667`. Eight years can
remain visible as reported tenure while two years appears as "used for score".

## 6. Combine components into the overall score

| Component | Default overall weight |
| --- | ---: |
| Semantic similarity | 45% |
| Weighted skill coverage | 40% |
| Explicit experience fit | 15% |

When all components are available, the formula is:

```text
Overall score ≈ 100 × (0.45 × S + 0.40 × K + 0.15 × E)
```

These weights are transparent design choices: semantics captures broader text
alignment, explicit skills provide a substantial auditable signal, and experience
has a smaller contribution because extraction is less reliable. The weights were
not learned from recruitment outcomes or tuned against the frozen challenge set.

### Missing-component handling

Missing evidence and missing requirements have different effects:

| Situation | Behavior |
| --- | --- |
| No recognized JD skills | Omit the skills component |
| No positive JD experience minimum | Omit the experience component |
| Required skill absent from resume | Keep skills active; the skill receives no coverage credit |
| JD requires experience but no applicable candidate claim exists | Keep experience active with score zero |
| Encoder fails | Return HTTP 503; do not substitute a fabricated semantic score |

Active weights are normalized to sum to one. The implementation computes each
contribution from the raw component value, rounds it to two decimal places, sums
those rounded contributions, and rounds the total to one decimal place:

```text
W = sum(default weights of active components)
normalized_weight_c = default_weight_c / W
contribution_c = round(100 × component_c × normalized_weight_c, 2)
overall_score = round(sum(contribution_c), 1)
```

Component percentages are displayed to two decimals and normalized weights are
returned to six decimals. Contributions are calculated before those display
roundings, so recomputing from rounded display percentages can differ slightly.

If experience is omitted, weights become `45/85` for semantics and `40/85` for
skills. If only semantics remains, its weight becomes 100%.

### Worked example

Suppose the JD requires Python, React and three years of experience, with Docker
desirable. The resume demonstrates Python and React, claims two applicable years,
and does not mention Docker. Assume an illustrative semantic similarity of 0.80.

| Component | Raw value | Percentage | Weight | Contribution |
| --- | ---: | ---: | ---: | ---: |
| Semantic | 0.80 | 80.00% | 45% | 36.00 |
| Skills | 2 / 2.25 | 88.89% | 40% | 35.56 |
| Experience | 2 / 3 | 66.67% | 15% | 10.00 |
| **Overall** | | | | **81.6 / 100** |

The semantic input is illustrative, not a claim that an actual model run will
produce 0.80 for a particular resume. A score of 81.6 is an alignment score, not
an 81.6% chance of being a successful hire.

## 7. Rank candidates and expose explanations

Candidates are sorted by final score descending. Equal final scores are ordered
by extracted candidate name. Searching the dashboard filters the existing ranking;
it does not recalculate scores or rank positions.

Each candidate result includes matched and missing skills, missing required and
desirable skills separately, reported and applicable experience, component scores,
normalized weights, point contributions, and explanation strings. Skill and
experience evidence includes verbatim snippets and one-based extracted-text line
numbers; these are not PDF page coordinates. Up to three skill passages per
recognized skill are retained.

Completed runs store these structured results in the configured database. Raw
uploaded files are not retained as resume documents, but extracted contact details
and evidence snippets are persisted. Old runs keep their original scores rather
than being silently recalculated when the algorithm changes.

## 8. Evaluation and practical limits

The separate challenge benchmark compares skills-only coverage, a TF-IDF hybrid,
and this embedding hybrid on three JDs and thirty synthetic resumes. The two
hybrids share the same skill and experience components, isolating the similarity
choice. Macro nDCG@5 is 0.626, 0.928 and 0.932 respectively. Both hybrids have
Precision@5 of 0.800, while embedding pairwise agreement is slightly lower.

The labels are assistant-authored and frozen before scoring, not independently
human validated. The small difference from TF-IDF does not establish broad
superiority. An NLP keyword-list profile still ranks too highly, and some
paraphrases rank poorly. See [the full evaluation and failure analysis](../evaluation/README.md).

Other limits include heuristic names, negation and priority cues; layout-dependent
text extraction; overlapping skill labels; no verified career timeline; no separate
qualification score; and no modeling of alternative skills or per-skill minimum
years. Name/email removal does not establish fairness: other text can contain
demographic proxies, and no bias audit has been performed.

## Implementation map

| Stage | Source |
| --- | --- |
| Upload extraction and limits | [`backend/parsing.py`](../backend/parsing.py) |
| Candidate fields and identity removal | [`backend/extraction.py`](../backend/extraction.py) |
| Skill aliases, detection and evidence | [`backend/taxonomy.py`](../backend/taxonomy.py), [`backend/skills.py`](../backend/skills.py) |
| JD priorities and minimums | [`backend/requirements.py`](../backend/requirements.py) |
| Experience claims and relevance | [`backend/experience.py`](../backend/experience.py) |
| Embedding inference and chunk similarity | [`backend/semantic.py`](../backend/semantic.py) |
| Weights, normalization and contributions | [`backend/scoring.py`](../backend/scoring.py) |
| Candidate assembly and sorting | [`backend/matching.py`](../backend/matching.py) |

[Back to architecture and setup](../README.md)
