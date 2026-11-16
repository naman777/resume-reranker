"""Render metrics and rankings with the unsuccessful cases visible."""

from pathlib import Path

METRIC_NAMES = ('ndcg_at_5', 'precision_at_5', 'pairwise_agreement')


def table(headers: list[str], rows: list[list]) -> list[str]:
    return [
        '| ' + ' | '.join(headers) + ' |',
        '| ' + ' | '.join('---' for _ in headers) + ' |',
        *['| ' + ' | '.join(map(str, row)) + ' |' for row in rows],
    ]


def metric_table(methods: dict, include_time: bool = False) -> list[str]:
    rows = []
    for name, result in methods.items():
        metrics = result['metrics'] if include_time else result
        row = [name, *[f'{metrics[metric]:.3f}' for metric in METRIC_NAMES]]
        if include_time:
            row.append(f'{result["seconds"]:.2f}')
        rows.append(row)
    headers = ['Method', 'nDCG@5', 'Precision@5', 'Pairwise agreement']
    return table(headers + (['Seconds'] if include_time else []), rows)


def role_section(role: dict) -> list[str]:
    lines = [f'### {role["title"]}', '', *metric_table(role['methods'], include_time=True)]
    for method, result in role['methods'].items():
        rows = [
            [item['candidate_id'], f'{item["score"]:.1f}', item['grade'], item['title']]
            for item in result['ranking'][:5]
        ]
        lines += ['', f'**{method}: top five**', '']
        lines += table(['Candidate', 'Score', 'Label', 'Title'], rows)
    return lines + ['']


def visible_errors(roles: list[dict]) -> list[str]:
    lines = ['## Visible errors in the application matcher', '']
    for role in roles:
        application = role['methods'].get('embedding_hybrid')
        if application is None:
            continue
        mistakes = [item for item in application['ranking'][:5] if item['grade'] < 2]
        descriptions = [
            f'{item["candidate_id"]} ({item["title"]}, grade {item["grade"]}, score {item["score"]})'
            for item in mistakes
        ]
        description = (
            ', '.join(descriptions) or 'no grade 0–1 candidates in the displayed top five.'
        )
        lines.append(f'- **{role["title"]}:** {description}')
    return lines


def markdown_report(report: dict) -> str:
    lines = [
        '# Ranking challenge results',
        '',
        '**Assistant-authored synthetic labels; not independently human validated.**',
        '',
        f'Dataset version: `{report["dataset"]["dataset_version"]}`. Generated: {report["generated_at"]}.',
        'Three roles, thirty resumes, ninety labeled role/resume pairs. Labels were frozen before scoring.',
        '',
        '## Macro averages across roles',
        '',
        *metric_table(report['macro']),
        '',
        'Metrics average over all possible orders inside exact score ties. Precision considers grades 2–3 relevant.',
        '',
        '## Results by role',
        '',
    ]
    for role in report['roles']:
        lines += role_section(role)
    rows = [
        [probe['role_id'], probe['better'], probe['worse'], method, outcome]
        for probe in report['probes']
        for method, outcome in probe['methods'].items()
    ]
    lines += ['## Predeclared contrast probes', '']
    lines += table(['Role', 'Preferred candidate', 'Comparator', 'Method', 'Outcome'], rows)
    lines += ['', *visible_errors(report['roles']), '', '## Interpretation limits', '']
    lines += [
        '- The same assistant authored cases and labels; external review is pending.',
        '- Existing application weights, aliases and heuristics were not tuned on this set.',
        '- Lexical hybrid changes only the similarity component; skills and experience logic is identical.',
        '- Skills-only also uses aliases, negation and priority weights, rather than raw substrings.',
        '- TF-IDF vocabulary is fitted without labels. The embedding model is pretrained, not trained here.',
        '- Metrics measure authored-rubric agreement, not hiring performance, fairness or probabilities.',
        '- Scores use one decimal. Displayed ties use candidate ID order; metrics average over ties.',
        '- Timings exclude model loading and are not production latency guarantees.',
        '- Complete rankings, components, judgments, hashes and versions are in the adjacent JSON.',
        '',
    ]
    return '\n'.join(lines)


def write_markdown(report: dict, output: Path) -> None:
    output.write_text(markdown_report(report), encoding='utf-8')
