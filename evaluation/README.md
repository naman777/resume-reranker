# Ranking evaluation

This evaluates ranking agreement on **three new JDs, thirty synthetic resumes and
ninety graded role/resume pairs**. It is separate from the ten demo/parser fixtures.
All methods rank all thirty candidates for every role, including cross-role profiles.

The cases and judgments were authored by the same assistant that implemented the
application. They were frozen before the first benchmark run, but they are **not
independent human ground truth**. No scoring weights, aliases or extraction rules
were changed after observing this challenge set.

## Run it

From the repository root, after installing the backend dependencies:

```bash
python -m evaluation.run
python -m evaluation.run --lexical-only
python -m pytest tests/test_evaluation.py -q
```

The complete run uses actual CPU embeddings and writes `results/benchmark.json`
and `results/benchmark.md`. The lexical-only run does not load or download a model
and uses separate `lexical-benchmark` output files. Pass `--output PATH.json` to
write a new result without replacing the checked-in reference run.

Neither command starts FastAPI, reads candidate data from Neon or saves a run to
the application database. Evaluation data is excluded from the production image.

## What is compared

| Method | Similarity | Skills | Experience |
| --- | --- | --- | --- |
| Skills only | None | Alias-aware required/desirable coverage | None |
| Lexical hybrid | TF-IDF cosine, word unigrams and bigrams | Application logic | Application logic |
| Embedding hybrid | MiniLM chunk embeddings | Application logic | Application logic |

The lexical and embedding hybrids use the application's unchanged 45/40/15
weights and the same missing-component behavior. Their difference isolates the
similarity component. Skills-only is a useful simpler baseline, but differences
from it cannot be attributed solely to embeddings because it also omits experience.

TF-IDF learns its vocabulary from each JD plus the candidate texts without labels.
Candidate identity removal is shared with the embedding scorer. Baseline functions
receive only filenames and resume text, never relevance grades or scenario tags.

## Labels and metrics

Grades are 0 (no demonstrated fit), 1 (limited/transferable fit), 2 (relevant partial
fit with a material gap), and 3 (strong demonstrated fit). Grades 2 and 3 count as
relevant for Precision@5. Each judgment has a rationale in `data/labels.json`.

- **nDCG@5:** rewards placing higher-grade candidates near the top, using gain
  `2^grade - 1` and logarithmic rank discounts. One is an ideal top-five ordering.
- **Precision@5:** fraction of the top five judged relevant by the authored rubric.
- **Pairwise agreement:** fraction of unequal-grade pairs ordered correctly.
  Score ties receive half credit; equal-grade pairs are excluded.

Metrics average over all possible orders within exact score ties, including ties
crossing position five. Candidate ID ordering cannot improve these metrics.
Macro results weight each of the three roles equally. None of these metrics is
a probability of hiring success or a measurement of fairness.

## Reference results and interpretation

The actual MiniLM benchmark was reproduced in the deployed Linux image without
network access and agreed with the initial local run:

| Method | nDCG@5 | Precision@5 | Pairwise agreement |
| --- | ---: | ---: | ---: |
| Skills only | 0.626 | 0.617 | 0.826 |
| Lexical hybrid | 0.928 | 0.800 | 0.915 |
| Embedding hybrid | 0.932 | 0.800 | 0.912 |

The embedding hybrid has only a **small** nDCG advantage over the lexical control,
equal top-five precision and slightly lower pairwise agreement. This set does not
establish a broad or statistically significant advantage for embeddings.

Examples worth discussing in an interview:

- **Semantic improvement:** for the Python role, the paraphrased service profile
  `c02` outranks the Java-specific `c03` under embeddings (47.2 versus 42.7), while
  both model-free baselines reverse them. Neither profile is a full stack match.
- **Keyword vulnerability:** the NLP keyword-list profile `c24`, labeled 0, still
  reaches third place with score 69.0 in the embedding hybrid. A bag of desirable
  terms is not sufficient evidence of delivery; a semantic score does not solve this.
- **Paraphrase failures:** all methods put frontend paraphrase `c12` below designer
  `c13`. Both hybrids put NLP paraphrase `c22` below analyst `c23`. Missing aliases,
  skill coverage and experience association can dominate semantic similarity.
- **Scope limitation:** the frontend top five contains junior `c15` and Node-service
  developer `c19`, both labeled 1. Shared TypeScript evidence does not establish
  the full React role, and relevant tenure is not a verified employment timeline.

The [generated report](results/benchmark.md) includes every role's top five,
all nine predeclared contrast probes and visible failures. The adjacent JSON has
all 270 method/role/candidate scores, component breakdowns, dataset hashes, source
fingerprints, dependency versions and the model revision. The result is reproducible
evidence about these cases, not a general accuracy claim.

## Independent review before stronger claims

```bash
python -m evaluation.review
```

This creates `evaluation/reviews/blind-review.csv` with ninety rows containing JDs
and resume text, but **no assistant labels or model scores**. Give it to a human
reviewer with the rubric above before showing them any results. Have them complete
the grade and rationale columns; record disagreements rather than silently replacing
them. Review files are ignored by Git by default.

After review, create an explicitly versioned dataset and seal its hashes before
running another evaluation. Do not edit v1 labels to make a preferred method win.
If the matcher is improved using v1 errors, treat v1 as development data and collect
a new untouched evaluation set. Agreement between multiple independent reviewers
and more roles are needed before making stronger claims.

## Integrity and automation

`data/manifest.json` stores canonical JSON SHA-256 hashes, so line-ending changes
do not break cross-platform checks. The runner rejects modified inputs or labels.
Hashes detect accidental drift; they are not proof of independent annotation or
cryptographic proof that a person could not have seen predictions.

GitHub Actions runs lint, formatting, backend/frontend tests, the frontend build
and a model-free benchmark on pushes and pull requests. A separate manually
triggered workflow runs the real embedding comparison and uploads complete reports.
These jobs need no Neon credentials. They report ranking metrics without using a
small authored dataset as an automatic hiring-quality gate.
