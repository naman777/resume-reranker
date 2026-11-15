import React from 'react';
import { afterEach, expect, it, vi } from 'vitest';
import { cleanup, render, screen, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import CandidateAnalysis from './CandidateAnalysis';
import JobRequirements from './JobRequirements';

afterEach(cleanup);

it('shows role-specific experience evidence and missing required skills', async () => {
  const user = userEvent.setup();
  const candidate = {
    name: 'Synthetic Candidate',
    email: null,
    qualifications: [],
    experience: 8,
    score: 70,
    required_experience: 3,
    matched_skills: ['Python'],
    missing_skills: ['React'],
    missing_required_skills: ['React'],
    breakdown: {},
    reasons: [],
    skill_evidence: { Python: [{ line: 3, text: 'Built Python services.' }] },
    experience_comparison: {
      years: 2,
      required_years: 3,
      basis: 'relevant_claim',
      limitation: 'Explicit claims only.',
      evidence: [{ line: 2, text: '2 years using Python' }],
    },
  };
  render(<CandidateAnalysis candidate={candidate} onClose={vi.fn()} />);

  expect(screen.getByText('Required skills not detected: React')).toBeTruthy();
  const evidence = screen.getByRole('region', { name: 'Resume evidence' });
  expect(within(evidence).getByText(/2 years compared with 3 required/)).toBeTruthy();
  expect(within(evidence).getByText('2 years using Python')).toBeTruthy();
  await user.click(within(evidence).getByText('Python'));
  expect(within(evidence).getByText('Built Python services.')).toBeTruthy();
  expect(within(evidence).getByText('Resume line 3')).toBeTruthy();
});

it('distinguishes required and desirable JD skills', () => {
  render(
    <JobRequirements
      requirements={{
        skills: ['Python', 'Docker'],
        required_skills: ['Python'],
        desirable_skills: ['Docker'],
        experience: 3,
        qualifications: [],
      }}
    />,
  );
  expect(screen.getByText('Required · full weight')).toBeTruthy();
  expect(screen.getByText('Desirable · quarter weight')).toBeTruthy();
  expect(screen.getByText('Python')).toBeTruthy();
  expect(screen.getByText('Docker')).toBeTruthy();
});
