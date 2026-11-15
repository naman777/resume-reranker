import { useState } from 'react';
import * as rankingsApi from '../api/rankings';
import { createSampleResumes, SAMPLE_JOB_DESCRIPTION } from '../data/samples';

/** Own the workspace workflow; presentation components receive data/actions. */
export function useMatchingWorkspace() {
  const [jobDescription, setJobDescription] = useState('');
  const [jobDescriptionFile, setJobDescriptionFile] = useState(null);
  const [resumeFiles, setResumeFiles] = useState([]);
  const [run, setRun] = useState(null);
  const [selectedCandidate, setSelectedCandidate] = useState(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const [history, setHistory] = useState([]);

  async function submit(event) {
    event.preventDefault();
    setBusy(true);
    setError('');
    setSelectedCandidate(null);

    try {
      const result = await rankingsApi.matchCandidates({
        jobDescription,
        jobDescriptionFile,
        resumeFiles,
      });
      setRun(result);
    } catch (error) {
      setError(error.message);
    } finally {
      setBusy(false);
    }
  }

  function loadDemo() {
    setJobDescription(SAMPLE_JOB_DESCRIPTION);
    setJobDescriptionFile(null);
    setResumeFiles(createSampleResumes());
    setError('');
  }

  async function loadHistory() {
    setError('');
    try {
      setHistory(await rankingsApi.listRuns());
    } catch (error) {
      setError(error.message);
    }
  }

  async function restoreRun(id) {
    setError('');
    try {
      setRun(await rankingsApi.getRun(id));
      setSelectedCandidate(null);
    } catch (error) {
      setError(error.message);
    }
  }

  async function deleteRun(id) {
    setError('');
    try {
      await rankingsApi.deleteRun(id);
      if (run?.id === id) {
        setRun(null);
        setSelectedCandidate(null);
      }
      await loadHistory();
    } catch (error) {
      setError(error.message);
    }
  }

  return {
    jobDescription,
    setJobDescription,
    jobDescriptionFile,
    setJobDescriptionFile,
    resumeFiles,
    setResumeFiles,
    run,
    selectedCandidate,
    setSelectedCandidate,
    busy,
    error,
    history,
    submit,
    loadDemo,
    loadHistory,
    restoreRun,
    deleteRun,
  };
}
