import React from 'react';
import SkillTags from './SkillTags';

export default function CandidateTable({ candidates, onSelect }) {
  return (
    <div className="tablewrap">
      <table>
        <thead>
          <tr>
            <th>RANK</th>
            <th>CANDIDATE</th>
            <th>EXPERIENCE</th>
            <th>MATCH</th>
            <th>MATCHED SKILLS</th>
            <th aria-label="Actions" />
          </tr>
        </thead>
        <tbody>
          {candidates.map(({ candidate, rank }) => (
            <tr key={rank}>
              <td>{rank}</td>
              <td>
                <b>{candidate.name}</b>
                <small>{candidate.filename}</small>
              </td>
              <td>
                {candidate.experience == null
                  ? 'Not found'
                  : `${candidate.experience} years`}
                {candidate.experience_comparison && (
                  <small>
                    Used for score:{' '}
                    {candidate.experience_comparison.years == null
                      ? 'None applicable'
                      : `${candidate.experience_comparison.years} years`}
                  </small>
                )}
              </td>
              <td>
                <strong className="score">{candidate.score}%</strong>
                <div className="meter">
                  <i style={{ width: `${candidate.score}%` }} />
                </div>
              </td>
              <td>
                <SkillTags skills={candidate.matched_skills} />
              </td>
              <td>
                <button type="button" onClick={() => onSelect(candidate)}>
                  View analysis ↗
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
