import React from 'react';

export default function WorkspaceLayout({ children, onLoadHistory }) {
  return (
    <>
      <aside>
        <div className="brand">
          s<span>shortlist</span>
        </div>
        <div className="nav active">▦ &nbsp; Candidate matching</div>
        <button type="button" className="nav" onClick={onLoadHistory}>
          ◷ &nbsp; Saved runs
        </button>
        <div className="sidefoot">
          ASSIGNMENT PROTOTYPE
          <br />
          <small>
            Explainable matching.
            <br />
            Human decisions.
          </small>
        </div>
      </aside>
      <main>
        <header>
          <span>WORKSPACE / CANDIDATE MATCHING</span>
          <span className="pill">● &nbsp; Local workspace</span>
        </header>
        {children}
        <footer>
          SHORTLIST / RESUME MATCHING PROTOTYPE
          <span>Built for transparent review.</span>
        </footer>
      </main>
    </>
  );
}
