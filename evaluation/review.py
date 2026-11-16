"""Export a blind review worksheet without model scores or assistant relevance labels."""

import argparse
import csv
from pathlib import Path

from evaluation.dataset import load_dataset


def export_review(output: Path) -> None:
    dataset = load_dataset()
    output.parent.mkdir(parents=True, exist_ok=True)
    fields = (
        'role_id',
        'candidate_id',
        'job_description',
        'resume_text',
        'reviewer_grade',
        'reviewer_rationale',
    )
    with output.open('w', newline='', encoding='utf-8-sig') as file:
        writer = csv.DictWriter(file, fieldnames=fields)
        writer.writeheader()
        for role in dataset['roles']:
            for resume in dataset['resumes']:
                writer.writerow(
                    {
                        'role_id': role['id'],
                        'candidate_id': resume['id'],
                        'job_description': role['text'],
                        'resume_text': resume['text'],
                        'reviewer_grade': '',
                        'reviewer_rationale': '',
                    }
                )


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=Path('evaluation/reviews/blind-review.csv'))
    export_review(parser.parse_args().output)
