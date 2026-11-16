import csv
import json
import math
import shutil

import pytest

from evaluation.baselines import lexical_scores, score_method
from evaluation.dataset import DATA_DIRECTORY, load_dataset, matcher_inputs
from evaluation.metrics import ranking_metrics
from evaluation.review import export_review


def test_challenge_set_is_frozen_complete_and_separate_from_demo():
    dataset = load_dataset()
    assert len(dataset['roles']) == 3
    assert len(dataset['resumes']) == 30
    assert sum(len(judgments) for judgments in dataset['labels']['judgments'].values()) == 90
    assert dataset['manifest']['independent_annotation'] is False
    assert len(dataset['probes']) == 9
    inputs = matcher_inputs(dataset['resumes'])
    assert all(set(candidate) == {'filename', 'text'} for candidate in inputs)
    assert all('Synthetic Candidate' not in candidate['text'] for candidate in inputs)


def test_annotation_edits_fail_manifest_validation(tmp_path):
    shutil.copytree(DATA_DIRECTORY, tmp_path / 'data')
    labels_path = tmp_path / 'data/labels.json'
    labels = json.loads(labels_path.read_text())
    labels['judgments']['python_backend']['c01']['grade'] = 0
    labels_path.write_text(json.dumps(labels))
    with pytest.raises(ValueError, match='Frozen dataset changed'):
        load_dataset(tmp_path / 'data')


def test_perfect_and_reversed_rankings():
    grades = {'a': 3, 'b': 2, 'c': 0}
    perfect = ranking_metrics({'a': 90, 'b': 50, 'c': 10}, grades, k=2)
    assert perfect['ndcg_at_2'] == pytest.approx(1)
    assert perfect['precision_at_2'] == 1
    assert perfect['pairwise_agreement'] == 1
    reversed_result = ranking_metrics({'a': 10, 'b': 50, 'c': 90}, grades, k=2)
    assert reversed_result['pairwise_agreement'] == 0
    assert reversed_result['precision_at_2'] == 0.5


def test_ties_are_averaged_at_the_cutoff_and_independent_of_id_order():
    grades = {'a': 3, 'b': 0}
    forward = ranking_metrics({'a': 50, 'b': 50}, grades, k=1)
    reverse = ranking_metrics({'b': 50, 'a': 50}, grades, k=1)
    assert forward == reverse
    assert forward['ndcg_at_1'] == 0.5
    assert forward['precision_at_1'] == 0.5
    assert forward['pairwise_agreement'] == 0.5


def test_no_relevant_candidates_and_bad_metric_inputs():
    assert ranking_metrics({'a': 10}, {'a': 0}, k=1)['ndcg_at_1'] == 0
    with pytest.raises(ValueError):
        ranking_metrics({'a': 1}, {'b': 1}, k=1)
    with pytest.raises(ValueError):
        ranking_metrics({'a': 1}, {'a': 1}, k=2)
    with pytest.raises(ValueError, match='finite'):
        ranking_metrics({'a': float('nan')}, {'a': 1}, k=1)
    with pytest.raises(ValueError, match='Grades'):
        ranking_metrics({'a': 1}, {'a': 4}, k=1)


def test_model_free_baselines_do_not_load_an_encoder(monkeypatch):
    def forbidden():
        pytest.fail('A model-free baseline attempted to load the embedding model.')

    monkeypatch.setattr('backend.semantic.model', forbidden)
    candidates = [
        {'filename': 'a.txt', 'text': 'Alex\nPython React developer with 3 years experience'}
    ]
    for method in ('skills_only', 'lexical_hybrid'):
        result = score_method(method, 'Python developer with 3 years experience', candidates)
        assert result[0]['candidate_id'] == 'a'
        assert 0 <= result[0]['score'] <= 100


def test_tfidf_handles_empty_and_unrelated_vocabulary():
    assert lexical_scores('the and', ['A\nthe or']) == [0.0]
    score = lexical_scores('Python backend services', ['Alex\nReact frontend interfaces'])[0]
    assert math.isclose(score, 0)


def test_blind_review_sheet_contains_no_labels_or_scores(tmp_path):
    output = tmp_path / 'review.csv'
    export_review(output)
    with output.open(encoding='utf-8-sig', newline='') as file:
        rows = list(csv.DictReader(file))
    assert len(rows) == 90
    assert set(rows[0]) == {
        'role_id',
        'candidate_id',
        'job_description',
        'resume_text',
        'reviewer_grade',
        'reviewer_rationale',
    }
    assert all(not row['reviewer_grade'] and not row['reviewer_rationale'] for row in rows)
