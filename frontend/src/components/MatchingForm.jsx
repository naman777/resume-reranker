import React from 'react';
import JobDescriptionInput from './JobDescriptionInput';
import ResumeUpload from './ResumeUpload';

export default function MatchingForm({
  jobDescription,
  onJobDescriptionChange,
  jobDescriptionFile,
  onJobDescriptionFileChange,
  resumeFiles,
  onResumeFilesChange,
  busy,
  onSubmit,
}) {
  const canSubmit =
    resumeFiles.length > 0 && (jobDescription.trim().length > 0 || jobDescriptionFile);

  return (
    <form onSubmit={onSubmit}>
      <div className="inputs">
        <JobDescriptionInput
          value={jobDescription}
          onChange={onJobDescriptionChange}
          file={jobDescriptionFile}
          onFileChange={onJobDescriptionFileChange}
        />
        <ResumeUpload files={resumeFiles} onChange={onResumeFilesChange} />
      </div>
      <div className="actionbar">
        <span>Semantic similarity + skills + experience</span>
        <button type="submit" className="primary" disabled={busy || !canSubmit}>
          {busy ? 'Analyzing resumes…' : 'Match candidates →'}
        </button>
      </div>
    </form>
  );
}
