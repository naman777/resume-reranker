"""Record versions and source fingerprints without reading runtime secrets."""

import hashlib
import json
import platform
import subprocess
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def provenance() -> dict:
    modules = (
        'matching',
        'scoring',
        'requirements',
        'extraction',
        'experience',
        'skills',
        'taxonomy',
        'evidence',
        'semantic',
    )
    sources = {
        name: (ROOT / 'backend' / f'{name}.py').read_text(encoding='utf-8') for name in modules
    }
    code_hash = hashlib.sha256(json.dumps(sources, sort_keys=True).encode()).hexdigest()
    evaluator_sources = {
        path.name: path.read_text(encoding='utf-8')
        for path in sorted((ROOT / 'evaluation').glob('*.py'))
    }
    evaluator_hash = hashlib.sha256(
        json.dumps(evaluator_sources, sort_keys=True).encode()
    ).hexdigest()
    packages = {}
    for name in (
        'sentence-transformers',
        'transformers',
        'torch',
        'numpy',
        'scikit-learn',
        'scipy',
    ):
        try:
            packages[name] = version(name)
        except PackageNotFoundError:
            packages[name] = None
    try:
        revision = subprocess.check_output(
            ['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True
        ).strip()
    except (OSError, subprocess.CalledProcessError):
        revision = 'unavailable'
    return {
        'git_revision': revision,
        'scoring_source_sha256': code_hash,
        'evaluator_source_sha256': evaluator_hash,
        'python': platform.python_version(),
        'dependencies': packages,
    }
