import React from 'react';

export default function SavedRuns({ runs, onRestore, onDelete }) {
  if (runs.length === 0) return null;

  return (
    <section className="history">
      <b>Saved runs</b>
      {runs.map((run) => (
        <div key={run.id}>
          <button type="button" onClick={() => onRestore(run.id)}>
            {new Date(run.created_at).toLocaleString()}
          </button>
          <button type="button" onClick={() => onDelete(run.id)}>
            Delete
          </button>
        </div>
      ))}
    </section>
  );
}
