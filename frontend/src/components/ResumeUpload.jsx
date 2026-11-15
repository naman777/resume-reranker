import React from 'react';

export default function ResumeUpload({ files, onChange }) {
  return (
    <section>
      <div className="sectiontitle">
        <span className="step">02</span>
        <h2>Add your candidates</h2>
      </div>
      <label className="upload">
        <span className="uploadicon">↥</span>
        <b>Choose resume files</b>
        <span>PDF, DOCX or TXT · up to 50 files · 5 MB each</span>
        <input
          aria-label="Upload resumes"
          type="file"
          multiple
          accept=".pdf,.docx,.txt"
          onChange={(event) => onChange(Array.from(event.target.files))}
        />
      </label>
      <div className="files">
        {files.length > 0 ? (
          <>
            <b>{files.length} resumes ready</b>
            <span>{files.map((file) => file.name).join(', ')}</span>
          </>
        ) : (
          <span>No resumes added yet</span>
        )}
      </div>
      <p className="hint">Text-based PDFs work best. Scanned documents need OCR.</p>
    </section>
  );
}
