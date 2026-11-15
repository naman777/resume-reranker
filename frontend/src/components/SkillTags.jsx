import React from 'react';

export default function SkillTags({ skills }) {
  return skills.map((skill) => (
    <span className="tag" key={skill}>
      {skill}
    </span>
  ));
}
