import candidates from './candidates.json';

export const SAMPLE_JOB_DESCRIPTION = `Full Stack Developer
Required skills: Python, FastAPI, React, PostgreSQL, REST APIs and Git.
Minimum 3 years of professional experience.
Nice to have: Docker, automated testing and natural language processing.
Qualifications: Bachelor degree in computer science or equivalent practical experience.
Build reliable backend services and accessible interfaces.`;

export function createSampleResumes() {
  return candidates.map(
    ({ id, text }) => new File([text], `${id}.txt`, { type: 'text/plain' }),
  );
}
