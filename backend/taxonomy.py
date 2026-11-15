"""Recognized aliases and education patterns; extend here for additional domains."""

SKILLS = {
    'Python': ['python'],
    'Java': ['java'],
    'JavaScript': ['javascript', 'js'],
    'TypeScript': ['typescript'],
    'React': ['react', 'reactjs', 'react.js'],
    'FastAPI': ['fastapi'],
    'Django': ['django'],
    'Spring Boot': ['spring boot'],
    'SQL': ['sql', 'postgresql', 'mysql', 'sqlite'],
    'PostgreSQL': ['postgresql', 'postgres'],
    'MongoDB': ['mongodb', 'mongo'],
    'Docker': ['docker', 'containerization'],
    'Kubernetes': ['kubernetes', 'k8s'],
    'AWS': ['aws', 'amazon web services'],
    'Git': ['git', 'github'],
    'REST APIs': ['rest', 'restful', 'rest api'],
    'Machine Learning': ['machine learning', 'ml'],
    'NLP': ['nlp', 'natural language processing'],
    'TensorFlow': ['tensorflow'],
    'PyTorch': ['pytorch'],
    'Node.js': ['node.js', 'nodejs'],
    'HTML': ['html'],
    'CSS': ['css'],
    'Redis': ['redis'],
    'Linux': ['linux'],
    'CI/CD': ['ci/cd', 'continuous integration', 'continuous delivery'],
    'Testing': ['pytest', 'unit testing', 'automated testing', 'jest'],
}

QUALIFICATIONS = {
    'Bachelor': r'\b(bachelor\w*|b\.?tech|b\.?sc|b\.?e\.)\b',
    'Master': r'\b(master\w*|m\.?tech|m\.?sc|mba)\b',
    'PhD': r'\b(ph\.?d|doctorate)\b',
}
