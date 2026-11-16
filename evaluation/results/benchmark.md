# Ranking challenge results

**Assistant-authored synthetic labels; not independently human validated.**

Dataset version: `1.0.0`. Generated: 2026-11-16T04:31:48.062130+00:00.
Three roles, thirty resumes, ninety labeled role/resume pairs. Labels were frozen before scoring.

## Macro averages across roles

| Method | nDCG@5 | Precision@5 | Pairwise agreement |
| --- | --- | --- | --- |
| skills_only | 0.626 | 0.617 | 0.826 |
| lexical_hybrid | 0.928 | 0.800 | 0.915 |
| embedding_hybrid | 0.932 | 0.800 | 0.912 |

Metrics average over all possible orders inside exact score ties. Precision considers grades 2–3 relevant.

## Results by role

### Python Backend Developer

| Method | nDCG@5 | Precision@5 | Pairwise agreement | Seconds |
| --- | --- | --- | --- | --- |
| skills_only | 0.670 | 0.650 | 0.785 | 0.29 |
| lexical_hybrid | 1.000 | 1.000 | 0.881 | 0.21 |
| embedding_hybrid | 1.000 | 1.000 | 0.898 | 1.63 |

**skills_only: top five**

| Candidate | Score | Label | Title |
| --- | --- | --- | --- |
| c01 | 100.0 | 3 | Production backend |
| c04 | 100.0 | 0 | Backend keyword list |
| c08 | 93.3 | 3 | Backend with frontend gap |
| c09 | 93.3 | 1 | Undated side project |
| c10 | 93.3 | 3 | Experienced returner |

**lexical_hybrid: top five**

| Candidate | Score | Label | Title |
| --- | --- | --- | --- |
| c01 | 63.6 | 3 | Production backend |
| c08 | 59.6 | 3 | Backend with frontend gap |
| c10 | 59.5 | 3 | Experienced returner |
| c17 | 55.4 | 2 | Split full-stack tenure |
| c07 | 52.5 | 2 | Django backend |

**embedding_hybrid: top five**

| Candidate | Score | Label | Title |
| --- | --- | --- | --- |
| c01 | 89.1 | 3 | Production backend |
| c08 | 88.0 | 3 | Backend with frontend gap |
| c10 | 86.6 | 3 | Experienced returner |
| c07 | 79.2 | 2 | Django backend |
| c17 | 79.2 | 2 | Split full-stack tenure |

### React Frontend Developer

| Method | nDCG@5 | Precision@5 | Pairwise agreement | Seconds |
| --- | --- | --- | --- | --- |
| skills_only | 0.558 | 0.500 | 0.900 | 0.07 |
| lexical_hybrid | 0.868 | 0.600 | 0.953 | 0.13 |
| embedding_hybrid | 0.894 | 0.600 | 0.958 | 1.40 |

**skills_only: top five**

| Candidate | Score | Label | Title |
| --- | --- | --- | --- |
| c14 | 100.0 | 0 | Frontend keyword list |
| c11 | 91.7 | 3 | Production React engineer |
| c16 | 91.7 | 3 | Accessible frontend specialist |
| c20 | 91.7 | 1 | Frontend course graduate |
| c15 | 87.5 | 1 | Junior React developer |

**lexical_hybrid: top five**

| Candidate | Score | Label | Title |
| --- | --- | --- | --- |
| c11 | 65.2 | 3 | Production React engineer |
| c16 | 61.3 | 3 | Accessible frontend specialist |
| c17 | 52.8 | 2 | Split full-stack tenure |
| c19 | 51.5 | 1 | Node service developer |
| c14 | 51.3 | 0 | Frontend keyword list |

**embedding_hybrid: top five**

| Candidate | Score | Label | Title |
| --- | --- | --- | --- |
| c11 | 84.1 | 3 | Production React engineer |
| c16 | 83.3 | 3 | Accessible frontend specialist |
| c17 | 73.9 | 2 | Split full-stack tenure |
| c15 | 73.1 | 1 | Junior React developer |
| c19 | 72.8 | 1 | Node service developer |

### Applied NLP Engineer

| Method | nDCG@5 | Precision@5 | Pairwise agreement | Seconds |
| --- | --- | --- | --- | --- |
| skills_only | 0.650 | 0.700 | 0.792 | 0.12 |
| lexical_hybrid | 0.916 | 0.800 | 0.912 | 0.08 |
| embedding_hybrid | 0.902 | 0.800 | 0.880 | 2.41 |

**skills_only: top five**

| Candidate | Score | Label | Title |
| --- | --- | --- | --- |
| c24 | 100.0 | 0 | ML keyword list |
| c21 | 78.3 | 3 | Production text retrieval engineer |
| c27 | 78.3 | 3 | Applied document ML engineer |
| c26 | 73.9 | 2 | Computer vision engineer |
| c25 | 52.2 | 1 | Research intern |

**lexical_hybrid: top five**

| Candidate | Score | Label | Title |
| --- | --- | --- | --- |
| c27 | 55.2 | 3 | Applied document ML engineer |
| c21 | 55.1 | 3 | Production text retrieval engineer |
| c26 | 53.0 | 2 | Computer vision engineer |
| c24 | 52.3 | 0 | ML keyword list |
| c29 | 42.6 | 2 | Text researcher without SQL |

**embedding_hybrid: top five**

| Candidate | Score | Label | Title |
| --- | --- | --- | --- |
| c21 | 72.6 | 3 | Production text retrieval engineer |
| c27 | 71.2 | 3 | Applied document ML engineer |
| c24 | 69.0 | 0 | ML keyword list |
| c26 | 62.0 | 2 | Computer vision engineer |
| c29 | 60.5 | 2 | Text researcher without SQL |

## Predeclared contrast probes

| Role | Preferred candidate | Comparator | Method | Outcome |
| --- | --- | --- | --- | --- |
| python_backend | c01 | c04 | skills_only | tie |
| python_backend | c01 | c04 | lexical_hybrid | pass |
| python_backend | c01 | c04 | embedding_hybrid | pass |
| python_backend | c02 | c03 | skills_only | fail |
| python_backend | c02 | c03 | lexical_hybrid | fail |
| python_backend | c02 | c03 | embedding_hybrid | pass |
| python_backend | c10 | c05 | skills_only | pass |
| python_backend | c10 | c05 | lexical_hybrid | pass |
| python_backend | c10 | c05 | embedding_hybrid | pass |
| react_frontend | c11 | c14 | skills_only | fail |
| react_frontend | c11 | c14 | lexical_hybrid | pass |
| react_frontend | c11 | c14 | embedding_hybrid | pass |
| react_frontend | c12 | c13 | skills_only | fail |
| react_frontend | c12 | c13 | lexical_hybrid | fail |
| react_frontend | c12 | c13 | embedding_hybrid | fail |
| react_frontend | c16 | c15 | skills_only | pass |
| react_frontend | c16 | c15 | lexical_hybrid | pass |
| react_frontend | c16 | c15 | embedding_hybrid | pass |
| nlp_engineer | c21 | c24 | skills_only | fail |
| nlp_engineer | c21 | c24 | lexical_hybrid | pass |
| nlp_engineer | c21 | c24 | embedding_hybrid | pass |
| nlp_engineer | c22 | c23 | skills_only | tie |
| nlp_engineer | c22 | c23 | lexical_hybrid | fail |
| nlp_engineer | c22 | c23 | embedding_hybrid | fail |
| nlp_engineer | c27 | c25 | skills_only | pass |
| nlp_engineer | c27 | c25 | lexical_hybrid | pass |
| nlp_engineer | c27 | c25 | embedding_hybrid | pass |

## Visible errors in the application matcher

- **Python Backend Developer:** no grade 0–1 candidates in the displayed top five.
- **React Frontend Developer:** c15 (Junior React developer, grade 1, score 73.1), c19 (Node service developer, grade 1, score 72.8)
- **Applied NLP Engineer:** c24 (ML keyword list, grade 0, score 69.0)

## Interpretation limits

- The same assistant authored cases and labels; external review is pending.
- Existing application weights, aliases and heuristics were not tuned on this set.
- Lexical hybrid changes only the similarity component; skills and experience logic is identical.
- Skills-only also uses aliases, negation and priority weights, rather than raw substrings.
- TF-IDF vocabulary is fitted without labels. The embedding model is pretrained, not trained here.
- Metrics measure authored-rubric agreement, not hiring performance, fairness or probabilities.
- Scores use one decimal. Displayed ties use candidate ID order; metrics average over ties.
- Timings exclude model loading and are not production latency guarantees.
- Complete rankings, components, judgments, hashes and versions are in the adjacent JSON.
