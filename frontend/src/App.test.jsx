import React from 'react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { cleanup, render, screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import App from './App';

const candidate = {
  name: 'Synthetic Candidate',
  filename: 'candidate.docx',
  email: 'sample@example.com',
  experience: 4,
  qualifications: ['Bachelor'],
  score: 91,
  matched_skills: ['Python'],
  missing_skills: ['React'],
  required_experience: 3,
  breakdown: { semantic: { score: 80, weight: 0.45, contribution: 36 } },
  reasons: ['Matched 1 of 2 recognized JD skills.'],
};

const savedRun = {
  id: 'test-run',
  created_at: '2026-11-15T10:00:00Z',
  requirements: { skills: ['Python', 'React'], experience: 3, qualifications: [] },
  candidates: [candidate],
  errors: [],
};

function respond(body, ok = true) {
  return Promise.resolve({ ok, json: async () => body });
}

beforeEach(() => vi.stubGlobal('fetch', vi.fn()));

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
});

describe('matching workspace', () => {
  it('submits ten samples, filters results, and opens candidate analysis', async () => {
    const user = userEvent.setup();
    fetch.mockImplementation(() => respond(savedRun));
    render(<App />);

    await user.click(screen.getByRole('button', { name: /Try 10 sample/ }));
    expect(screen.getByText('10 resumes ready')).toBeTruthy();
    await user.click(screen.getByRole('button', { name: /Match candidates/ }));
    await screen.findByRole('heading', { name: '1 candidates ranked' });

    const [path, options] = fetch.mock.calls[0];
    expect(path).toBe('/api/match');
    expect(options.method).toBe('POST');
    expect(options.body.getAll('resumes')).toHaveLength(10);
    expect(options.body.get('jd')).toContain('Full Stack Developer');

    await user.click(screen.getByRole('button', { name: /View analysis/ }));
    const dialog = screen.getByRole('dialog', { name: 'Candidate analysis' });
    expect(within(dialog).getByText(/sample@example.com/)).toBeTruthy();
    expect(dialog.textContent).toContain('React');
    await user.click(within(dialog).getByRole('button', { name: /Close/ }));
    expect(screen.queryByRole('dialog')).toBeNull();

    await user.type(
      screen.getByRole('textbox', { name: 'Search candidates' }),
      'missing',
    );
    expect(screen.getByText('No candidates match this search.')).toBeTruthy();
  });

  it('shows match errors and allows retry after a failed request', async () => {
    const user = userEvent.setup();
    fetch.mockImplementation(() =>
      respond({ detail: 'Semantic model unavailable.' }, false),
    );
    render(<App />);

    await user.click(screen.getByRole('button', { name: /Try 10 sample/ }));
    await user.click(screen.getByRole('button', { name: /Match candidates/ }));
    expect((await screen.findByRole('alert')).textContent).toBe(
      'Semantic model unavailable.',
    );
    expect(screen.getByRole('button', { name: /Match candidates/ }).disabled).toBe(false);
  });

  it('restores runs, reports failed deletion, and clears results after successful deletion', async () => {
    const user = userEvent.setup();
    fetch.mockImplementation((path, options) => {
      if (options?.method === 'DELETE') {
        return respond({ detail: 'Could not delete run' }, false);
      }
      return respond(path === '/api/runs' ? [savedRun] : savedRun);
    });
    render(<App />);

    await user.click(screen.getByRole('button', { name: /Saved runs/ }));
    const dateLabel = new Date(savedRun.created_at).toLocaleString();
    await user.click(await screen.findByRole('button', { name: dateLabel }));
    await screen.findByRole('heading', { name: '1 candidates ranked' });

    await user.click(screen.getByRole('button', { name: 'Delete' }));
    expect((await screen.findByRole('alert')).textContent).toBe('Could not delete run');
    expect(screen.getByRole('heading', { name: '1 candidates ranked' })).toBeTruthy();

    fetch.mockImplementation((path, options) =>
      respond(options?.method === 'DELETE' ? { deleted: true } : []),
    );
    await user.click(screen.getByRole('button', { name: 'Delete' }));
    await waitFor(() => {
      expect(screen.queryByRole('heading', { name: '1 candidates ranked' })).toBeNull();
      expect(screen.queryByRole('button', { name: 'Delete' })).toBeNull();
    });
  });
});
