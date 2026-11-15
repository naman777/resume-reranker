"""Explainable matching. No demographic/contact attributes enter scoring."""
import os
import re
from functools import lru_cache
import numpy as np

SKILLS = {
    'Python': ['python'], 'Java': ['java'], 'JavaScript': ['javascript', 'js'],
    'TypeScript': ['typescript'], 'React': ['react', 'reactjs', 'react.js'],
    'FastAPI': ['fastapi'], 'Django': ['django'], 'Spring Boot': ['spring boot'],
    'SQL': ['sql', 'postgresql', 'mysql', 'sqlite'], 'PostgreSQL': ['postgresql', 'postgres'],
    'MongoDB': ['mongodb', 'mongo'], 'Docker': ['docker', 'containerization'],
    'Kubernetes': ['kubernetes', 'k8s'], 'AWS': ['aws', 'amazon web services'],
    'Git': ['git', 'github'], 'REST APIs': ['rest', 'restful', 'rest api'],
    'Machine Learning': ['machine learning', 'ml'], 'NLP': ['nlp', 'natural language processing'],
    'TensorFlow': ['tensorflow'], 'PyTorch': ['pytorch'], 'Node.js': ['node.js', 'nodejs'],
    'HTML': ['html'], 'CSS': ['css'], 'Redis': ['redis'], 'Linux': ['linux'],
    'CI/CD': ['ci/cd', 'continuous integration', 'continuous delivery'],
    'Testing': ['pytest', 'unit testing', 'automated testing', 'jest'],
}
QUALIFICATIONS = {'Bachelor': r"\b(bachelor\w*|b\.?tech|b\.?sc|b\.?e\.)\b", 'Master': r"\b(master\w*|m\.?tech|m\.?sc|mba)\b", 'PhD': r'\b(ph\.?d|doctorate)\b'}


def skills(text):
    return [skill for skill, aliases in SKILLS.items() if any(re.search(r'(?<!\w)' + re.escape(alias) + r'(?!\w)', text, re.I) for alias in aliases)]


def experience(text):
    # Explicit claims only: avoids adding overlapping jobs or interpreting graduation years.
    values = re.findall(r'\b(\d+(?:\.\d+)?)\s*\+?\s*(?:years?|yrs?)\b', text, re.I)
    return max(map(float, values), default=None)


def extract(text, filename=''):
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    return {
        'name': lines[0][:100] if lines else filename,
        'email': next(iter(re.findall(r'[\w.+-]+@[\w.-]+\.[a-zA-Z]{2,}', text)), None),
        'experience': experience(text), 'skills': skills(text),
        'qualifications': [k for k, v in QUALIFICATIONS.items() if re.search(v, text, re.I)],
    }


def scoring_text(text):
    text = re.sub(r'[\w.+-]+@[\w.-]+\.[a-zA-Z]{2,}', '', text)
    lines = text.splitlines()
    # Candidate name is conventionally the first line. Suppress it in semantic matching.
    return '\n'.join(lines[1:]) if len(lines) > 1 else text


@lru_cache(maxsize=1)
def model():
    from sentence_transformers import SentenceTransformer
    return SentenceTransformer(os.getenv('EMBEDDING_MODEL', 'sentence-transformers/all-MiniLM-L6-v2'), device='cpu')


def chunks(text):
    words = text.split()
    return [' '.join(words[i:i+180]) for i in range(0, len(words), 140)] or ['']


def semantic_scores(jd, texts):
    encoder = model()
    job = encoder.encode(chunks(jd), normalize_embeddings=True)
    scores = []
    for text in texts:
        resume = encoder.encode(chunks(scoring_text(text)), normalize_embeddings=True)
        # Each JD chunk gets its best supporting resume chunk, then average.
        scores.append(float(np.clip((job @ resume.T).max(axis=1).mean(), 0, 1)))
    return scores


def rank(jd, candidates, semantic_fn=semantic_scores):
    requirements = extract(jd)
    required = requirements['skills']
    sem = semantic_fn(jd, [c['text'] for c in candidates])
    results = []
    for candidate, similarity in zip(candidates, sem):
        info = extract(candidate['text'], candidate['filename'])
        matched = sorted(set(required) & set(info['skills']))
        missing = sorted(set(required) - set(info['skills']))
        skill_score = len(matched) / len(required) if required else None
        needed, actual = requirements['experience'], info['experience']
        exp_score = min(actual / needed, 1) if needed and actual is not None else (0 if needed else None)
        components = [('semantic', float(similarity), .45), ('skills', skill_score, .40), ('experience', exp_score, .15)]
        weight = sum(w for _, s, w in components if s is not None)
        breakdown = {k: {'score': round(s*100, 2), 'weight': round(w/weight, 6), 'contribution': round(s*w/weight*100, 2)} for k, s, w in components if s is not None}
        score = round(sum(v['contribution'] for v in breakdown.values()), 1)
        results.append({**info, 'filename': candidate['filename'], 'score': score, 'matched_skills': matched,
                        'missing_skills': missing, 'required_experience': needed, 'breakdown': breakdown,
                        'reasons': [f"Matched {len(matched)} of {len(required)} recognized JD skills.",
                                    f"Semantic similarity: {similarity*100:.1f}% (text similarity, not probability of success).",
                                    f"Explicit experience: {actual if actual is not None else 'not found'} years; JD: {needed if needed else 'not specified'}."]})
    return requirements, sorted(results, key=lambda x: (-x['score'], x['name']))
