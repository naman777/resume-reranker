"""Cached sentence embeddings and chunk-based semantic similarity."""

import os
from functools import lru_cache

import numpy as np

from backend.extraction import scoring_text

CHUNK_WORDS = 180
CHUNK_OVERLAP_WORDS = 40


@lru_cache(maxsize=1)
def model():
    from sentence_transformers import SentenceTransformer

    return SentenceTransformer(
        os.getenv('EMBEDDING_MODEL', 'sentence-transformers/all-MiniLM-L6-v2'), device='cpu'
    )


def chunks(text: str) -> list[str]:
    words = text.split()
    stride = CHUNK_WORDS - CHUNK_OVERLAP_WORDS
    return [' '.join(words[i : i + CHUNK_WORDS]) for i in range(0, len(words), stride)] or ['']


def semantic_scores(jd: str, texts: list[str]) -> list[float]:
    encoder = model()
    job = encoder.encode(chunks(jd), normalize_embeddings=True)
    scores = []
    for text in texts:
        resume = encoder.encode(chunks(scoring_text(text)), normalize_embeddings=True)
        # Each JD chunk gets its best supporting resume chunk, then average.
        scores.append(float(np.clip((job @ resume.T).max(axis=1).mean(), 0, 1)))
    return scores
