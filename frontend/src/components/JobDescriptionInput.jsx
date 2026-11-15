import React from 'react';

export default function JobDescriptionInput({ value, onChange, file, onFileChange }) {
  return (
    <section>
      <div className="sectiontitle">
        <span className="step">01</span>
        <h2>Define the role</h2>
      </div>
      <label htmlFor="jd">Job description</label>
      <textarea
        id="jd"
        value={value}
        onChange={(event) => onChange(event.target.value)}
        placeholder="Paste the job description, required skills, and experience…"
      />
      <label className="filelabel">
        Or upload a job description
        <input
          type="file"
          accept=".pdf,.docx,.txt"
          onChange={(event) => onFileChange(event.target.files[0] || null)}
        />
      </label>
      {file && <small>{file.name} will replace pasted text.</small>}
    </section>
  );
}
