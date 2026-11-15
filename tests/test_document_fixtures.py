import asyncio

from samples.evaluate import evaluate


def test_generated_documents_match_expected_candidate_fields():
    report = asyncio.run(evaluate())
    assert report['failures'] == []
