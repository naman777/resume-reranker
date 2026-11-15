import React from 'react';
import ResumeEvidence from './ResumeEvidence';

export default function CandidateAnalysis({ candidate, onClose }) {
  return (
    <div className="overlay" onClick={onClose}>
      <section
        role="dialog"
        aria-modal="true"
        aria-label="Candidate analysis"
        className="dialog"
        onClick={(event) => event.stopPropagation()}
      >
        <button type="button" autoFocus className="close" onClick={onClose}>
          Close ×
        </button>
        <div className="eyebrow">CANDIDATE ANALYSIS</div>
        <h2>{candidate.name}</h2>
        <p>
          {candidate.email || 'Email not detected'} ·{' '}
          {candidate.qualifications.join(', ') || 'Qualification not detected'}
        </p>
        <div className="bigscore">
          {candidate.score}
          <small>/100</small>
        </div>
        <p>
          Reported experience: {candidate.experience ?? 'Unknown'} years. JD minimum:{' '}
          {candidate.required_experience ?? 'Unspecified'} years.
        </p>

        <h3>Matched skills</h3>
        {candidate.matched_skills.join(' · ') || 'None detected'}
        <h3>Missing skills</h3>
        {candidate.missing_skills.join(' · ') || 'No recognized JD skills missing'}
        {candidate.missing_required_skills?.length > 0 && (
          <p className="error">
            Required skills not detected: {candidate.missing_required_skills.join(', ')}
          </p>
        )}

        <h3>How this score was calculated</h3>
        {Object.entries(candidate.breakdown).map(([name, component]) => (
          <p key={name}>
            {name}: {component.score}% × {(component.weight * 100).toFixed(1)}%
            {' weight = '}
            <b>{component.contribution} points</b>
          </p>
        ))}

        <ResumeEvidence candidate={candidate} />

        <h3>Evidence & limitations</h3>
        {candidate.reasons.map((reason) => (
          <p key={reason}>{reason}</p>
        ))}
        <p className="hint">
          Experience uses explicit year claims, not a verified work timeline. Missing
          skills mean not detected, not absent.
        </p>
      </section>
    </div>
  );
}
