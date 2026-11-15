/** Read API responses consistently, including FastAPI's structured errors. */
async function request(path, options) {
  const response = await fetch(`/api${path}`, options);
  const body = await response.json();

  if (!response.ok) {
    const detail = body.detail ?? 'Request failed. Please try again.';
    throw new Error(typeof detail === 'string' ? detail : JSON.stringify(detail));
  }

  return body;
}

export function matchCandidates({ jobDescription, jobDescriptionFile, resumeFiles }) {
  const form = new FormData();
  form.append('jd', jobDescription);

  if (jobDescriptionFile) {
    form.append('jd_file', jobDescriptionFile);
  }
  resumeFiles.forEach((file) => form.append('resumes', file));

  return request('/match', { method: 'POST', body: form });
}

export function listRuns() {
  return request('/runs');
}

export function getRun(id) {
  return request(`/runs/${encodeURIComponent(id)}`);
}

export function deleteRun(id) {
  return request(`/runs/${encodeURIComponent(id)}`, { method: 'DELETE' });
}
