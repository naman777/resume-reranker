import React from 'react';

export default function ResumeEvidence({ candidate }) {
  const comparison = candidate.experience_comparison;
  const evidence = candidate.skill_evidence;

  if (!comparison && !evidence) return null;

  return (
    <section className="resume-evidence" aria-label="Resume evidence">
      <h3>Experience used in scoring</h3>
      {comparison && (
        <>
          <p>
            {comparison.years ?? 'Unknown'} years compared with{' '}
            {comparison.required_years ?? 'unspecified'} required.
            {comparison.basis === 'general_claim' &&
              ' This is a general experience claim; role relevance is unverified.'}
            {comparison.basis === 'unrelated_or_missing' &&
              ' No applicable experience claim was detected.'}
          </p>
          {comparison.evidence.map((claim, index) => (
            <blockquote key={index}>
              {claim.text}
              <small>Resume line {claim.line}</small>
            </blockquote>
          ))}
          <p className="hint">{comparison.limitation}</p>
        </>
      )}

      <h3>Supporting skill passages</h3>
      {candidate.matched_skills.map((skill) => (
        <details key={skill}>
          <summary>{skill}</summary>
          {(evidence?.[skill] ?? []).map((passage, index) => (
            <blockquote key={index}>
              {passage.text}
              <small>Resume line {passage.line}</small>
            </blockquote>
          ))}
        </details>
      ))}
    </section>
  );
}
