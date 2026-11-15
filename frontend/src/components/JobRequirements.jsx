import React from 'react';
import SkillTags from './SkillTags';

export default function JobRequirements({ requirements }) {
  return (
    <div className="requirements">
      <b>Recognized JD skills</b>
      <div>
        {requirements.required_skills ? (
          <>
            <p>Required · full weight</p>
            <SkillTags skills={requirements.required_skills} />
            {requirements.required_skills.length === 0 && <span>None detected</span>}
            {requirements.desirable_skills.length > 0 && (
              <>
                <p>Desirable · quarter weight</p>
                <SkillTags skills={requirements.desirable_skills} />
              </>
            )}
          </>
        ) : requirements.skills.length > 0 ? (
          <SkillTags skills={requirements.skills} />
        ) : (
          'None recognized; skills weight redistributed.'
        )}
      </div>
      <small>
        Experience: {requirements.experience ?? 'not specified'} years
        {' · '}Qualifications: {requirements.qualifications.join(', ') || 'not detected'}
      </small>
    </div>
  );
}
