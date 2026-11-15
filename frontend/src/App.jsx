import React from 'react';
import CandidateAnalysis from './components/CandidateAnalysis';
import MatchingForm from './components/MatchingForm';
import RankingResults from './components/RankingResults';
import SavedRuns from './components/SavedRuns';
import WorkspaceLayout from './components/WorkspaceLayout';
import { useMatchingWorkspace } from './hooks/useMatchingWorkspace';
import { exportRanking } from './utils/exportRanking';

export default function App() {
  const workspace = useMatchingWorkspace();

  return (
    <WorkspaceLayout onLoadHistory={workspace.loadHistory}>
      <div className="intro">
        <div>
          <div className="eyebrow">A CLEARER PATH TO YOUR SHORTLIST</div>
          <h1>Find the right fit.</h1>
          <p>Compare resumes with your role. Understand every match.</p>
        </div>
        <button
          type="button"
          className="secondary"
          onClick={workspace.loadDemo}
          disabled={workspace.busy}
        >
          Try 10 sample candidates ↗
        </button>
      </div>

      <div className="notice">
        Use synthetic or publicly licensed resumes for this assignment. Scores support
        review; they are not hiring recommendations.
      </div>

      <SavedRuns
        runs={workspace.history}
        onRestore={workspace.restoreRun}
        onDelete={workspace.deleteRun}
      />
      <MatchingForm
        jobDescription={workspace.jobDescription}
        onJobDescriptionChange={workspace.setJobDescription}
        jobDescriptionFile={workspace.jobDescriptionFile}
        onJobDescriptionFileChange={workspace.setJobDescriptionFile}
        resumeFiles={workspace.resumeFiles}
        onResumeFilesChange={workspace.setResumeFiles}
        busy={workspace.busy}
        onSubmit={workspace.submit}
      />

      {workspace.busy && (
        <p role="status">
          Loading the embedding model and comparing candidates. The first run can take a
          few minutes.
        </p>
      )}
      {workspace.error && (
        <div className="error" role="alert">
          {workspace.error}
        </div>
      )}
      {workspace.run && (
        <RankingResults
          run={workspace.run}
          onSelectCandidate={workspace.setSelectedCandidate}
          onExport={() => exportRanking(workspace.run)}
        />
      )}
      {workspace.selectedCandidate && (
        <CandidateAnalysis
          candidate={workspace.selectedCandidate}
          onClose={() => workspace.setSelectedCandidate(null)}
        />
      )}
    </WorkspaceLayout>
  );
}
