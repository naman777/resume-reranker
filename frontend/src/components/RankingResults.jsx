import React, { useState } from 'react';
import CandidateTable from './CandidateTable';
import JobRequirements from './JobRequirements';

export default function RankingResults({ run, onSelectCandidate, onExport }) {
  const [query, setQuery] = useState('');
  const search = query.toLowerCase();
  // Assign ranks before filtering so search preserves the original ranking.
  const candidates = run.candidates
    .map((candidate, index) => ({ candidate, rank: index + 1 }))
    .filter(({ candidate }) =>
      `${candidate.name} ${candidate.matched_skills.join(' ')}`
        .toLowerCase()
        .includes(search),
    );

  return (
    <section className="results">
      <div className="resulthead">
        <div>
          <div className="eyebrow">YOUR SHORTLIST</div>
          <h2>{run.candidates.length} candidates ranked</h2>
        </div>
        <button type="button" onClick={onExport}>
          Export analysis ↓
        </button>
      </div>
      <JobRequirements requirements={run.requirements} />
      {run.errors.map((error, index) => (
        <p className="error" key={index}>
          {error.filename}: {error.error}
        </p>
      ))}
      <input
        className="search"
        aria-label="Search candidates"
        placeholder="Search candidates or matched skills"
        value={query}
        onChange={(event) => setQuery(event.target.value)}
      />
      <CandidateTable candidates={candidates} onSelect={onSelectCandidate} />
      {candidates.length === 0 && <p>No candidates match this search.</p>}
      <p className="hint">
        Scores are relative text alignment, not calibrated probabilities. Review the
        evidence and missing information.
      </p>
    </section>
  );
}
