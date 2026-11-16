"""Validate frozen challenge data and keep labels outside matcher inputs."""

import hashlib
import json
from pathlib import Path

DATA_DIRECTORY = Path(__file__).resolve().parent / 'data'
DATA_FILES = ('roles.json', 'resumes.json', 'labels.json', 'probes.json')


def canonical_hash(value: object) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False)
    return hashlib.sha256(payload.encode('utf-8')).hexdigest()


def load_dataset(directory: Path = DATA_DIRECTORY) -> dict:
    manifest = json.loads((directory / 'manifest.json').read_text(encoding='utf-8'))
    documents = {}
    for filename in DATA_FILES:
        value = json.loads((directory / filename).read_text(encoding='utf-8'))
        if canonical_hash(value) != manifest['sha256'].get(filename):
            raise ValueError(
                f'Frozen dataset changed: {filename}. Create a new version explicitly.'
            )
        documents[filename] = value
    roles, resumes = documents['roles.json'], documents['resumes.json']
    labels, probes = documents['labels.json'], documents['probes.json']
    role_ids = {role['id'] for role in roles}
    resume_ids = {resume['id'] for resume in resumes}
    if len(roles) != 3 or len(role_ids) != 3 or len(resumes) != 30 or len(resume_ids) != 30:
        raise ValueError('Expected three unique roles and thirty unique resumes.')
    if set(labels['judgments']) != role_ids:
        raise ValueError('Judgments must cover every role.')
    for judgments in labels['judgments'].values():
        if set(judgments) != resume_ids:
            raise ValueError('Every role must judge all thirty resumes.')
        for judgment in judgments.values():
            if type(judgment['grade']) is not int or judgment['grade'] not in range(4):
                raise ValueError('Relevance grades must be integers from zero through three.')
            if not judgment['rationale'].strip():
                raise ValueError('Each judgment needs a written rationale.')
    for probe in probes:
        judgments = labels['judgments'][probe['role_id']]
        if judgments[probe['better']]['grade'] <= judgments[probe['worse']]['grade']:
            raise ValueError('Probe ordering must agree with the frozen relevance labels.')
    return {
        'manifest': manifest,
        'roles': roles,
        'resumes': resumes,
        'labels': labels,
        'probes': probes,
    }


def matcher_inputs(resumes: list[dict]) -> list[dict]:
    """Strip titles, scenario tags and any future annotation fields before scoring."""
    return [{'filename': resume['id'] + '.txt', 'text': resume['text']} for resume in resumes]
