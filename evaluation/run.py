"""Run frozen ranking comparisons: python -m evaluation.run [--lexical-only]."""

import argparse
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from time import perf_counter

from evaluation.baselines import METHODS, score_method
from evaluation.dataset import load_dataset, matcher_inputs
from evaluation.metrics import ranking_metrics
from evaluation.provenance import provenance
from evaluation.reporting import write_markdown

ROOT = Path(__file__).resolve().parents[1]


def evaluate_role(role: dict, candidates: list[dict], dataset: dict, methods: list[str]) -> dict:
    judgments = dataset['labels']['judgments'][role['id']]
    grades = {identifier: judgment['grade'] for identifier, judgment in judgments.items()}
    titles = {resume['id']: resume['title'] for resume in dataset['resumes']}
    results = {}
    for method in methods:
        started = perf_counter()
        ranked = score_method(method, role['text'], candidates)
        elapsed = perf_counter() - started
        scores = {candidate['candidate_id']: candidate['score'] for candidate in ranked}
        metrics = ranking_metrics(scores, grades)
        ranked.sort(key=lambda candidate: (-candidate['score'], candidate['candidate_id']))
        # Attach labels only after the matcher has finished; neither baseline receives them.
        annotated = [
            {
                **candidate,
                'title': titles[candidate['candidate_id']],
                **judgments[candidate['candidate_id']],
            }
            for candidate in ranked
        ]
        results[method] = {'metrics': metrics, 'seconds': round(elapsed, 4), 'ranking': annotated}
    return {'id': role['id'], 'title': role['title'], 'methods': results}


def evaluate_probes(probes: list[dict], roles: list[dict]) -> list[dict]:
    indexed = {role['id']: role for role in roles}
    results = []
    for probe in probes:
        outcomes = {}
        for method, result in indexed[probe['role_id']]['methods'].items():
            scores = {
                candidate['candidate_id']: candidate['score'] for candidate in result['ranking']
            }
            delta = scores[probe['better']] - scores[probe['worse']]
            outcomes[method] = 'pass' if delta > 0 else ('tie' if delta == 0 else 'fail')
        results.append({**probe, 'methods': outcomes})
    return results


def run_benchmark(lexical_only: bool = False) -> dict:
    dataset = load_dataset()
    methods = list(METHODS)[:2] if lexical_only else list(METHODS)
    model_metadata = None
    if not lexical_only:
        from backend.semantic import model

        started = perf_counter()
        encoder = model()
        configuration = encoder[0].auto_model.config
        dimension_function = getattr(encoder, 'get_embedding_dimension', None)
        if dimension_function is None:
            dimension_function = encoder.get_sentence_embedding_dimension
        model_metadata = {
            'name': os.getenv('EMBEDDING_MODEL', 'sentence-transformers/all-MiniLM-L6-v2'),
            'revision': getattr(configuration, '_commit_hash', None),
            'dimensions': dimension_function(),
            'load_seconds': round(perf_counter() - started, 4),
        }
    candidates = matcher_inputs(dataset['resumes'])
    roles = [evaluate_role(role, candidates, dataset, methods) for role in dataset['roles']]
    macro = {
        method: {
            metric: sum(role['methods'][method]['metrics'][metric] for role in roles) / len(roles)
            for metric in ('ndcg_at_5', 'precision_at_5', 'pairwise_agreement')
        }
        for method in methods
    }
    return {
        'generated_at': datetime.now(timezone.utc).isoformat(),
        'dataset': dataset['manifest'],
        'provenance': provenance(),
        'model': model_metadata,
        'methods': {method: METHODS[method] for method in methods},
        'macro': macro,
        'roles': roles,
        'probes': evaluate_probes(dataset['probes'], roles),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        '--lexical-only', action='store_true', help='Skip the embedding model entirely.'
    )
    parser.add_argument('--output', type=Path)
    arguments = parser.parse_args()
    if arguments.output is None:
        filename = 'lexical-benchmark.json' if arguments.lexical_only else 'benchmark.json'
        arguments.output = ROOT / 'evaluation/results' / filename
    report = run_benchmark(arguments.lexical_only)
    arguments.output.parent.mkdir(parents=True, exist_ok=True)
    arguments.output.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    write_markdown(report, arguments.output.with_suffix('.md'))
    print(json.dumps(report['macro'], indent=2))
    print(f'Complete rankings and report: {arguments.output}')


if __name__ == '__main__':
    main()
