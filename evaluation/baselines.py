"""Two model-free baselines and the unchanged application matcher."""

from pathlib import Path

import numpy as np

from backend.extraction import extract, scoring_text
from backend.matching import rank
from backend.requirements import extract_requirements
from backend.scoring import skill_coverage

METHODS = {
    'skills_only': 'Alias-aware weighted skill coverage',
    'lexical_hybrid': 'TF-IDF hybrid (same skills and experience)',
    'embedding_hybrid': 'Sentence Transformer hybrid (application)',
}


def lexical_scores(jd: str, texts: list[str]) -> list[float]:
    from sklearn.feature_extraction.text import TfidfVectorizer

    vectorizer = TfidfVectorizer(stop_words='english', ngram_range=(1, 2), sublinear_tf=True)
    try:
        vectors = vectorizer.fit_transform([jd, *map(scoring_text, texts)])
    except ValueError as error:
        if 'empty vocabulary' not in str(error):
            raise
        return [0.0] * len(texts)
    # L2-normalized TF-IDF vectors make the dot product cosine similarity.
    return np.clip((vectors[1:] @ vectors[0].T).toarray().ravel(), 0, 1).tolist()


def score_method(method: str, jd: str, candidates: list[dict]) -> list[dict]:
    if method == 'skills_only':
        requirements = extract_requirements(jd)
        results = []
        for candidate in candidates:
            information = extract(candidate['text'], candidate['filename'])
            matched = sorted(set(requirements['skills']) & set(information['skills']))
            coverage = skill_coverage(matched, requirements)
            results.append(
                {'filename': candidate['filename'], 'score': round((coverage or 0) * 100, 1)}
            )
    elif method == 'lexical_hybrid':
        _, results = rank(jd, candidates, semantic_fn=lexical_scores)
    elif method == 'embedding_hybrid':
        _, results = rank(jd, candidates)
    else:
        raise ValueError(f'Unknown method: {method}')
    return [
        {
            'candidate_id': Path(result['filename']).stem,
            'score': result['score'],
            **{
                key: result[key]
                for key in (
                    'breakdown',
                    'matched_skills',
                    'missing_required_skills',
                    'experience_comparison',
                )
                if key in result
            },
        }
        for result in results
    ]
