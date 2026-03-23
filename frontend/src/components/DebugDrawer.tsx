import React from 'react';
import useStore from '../store/useStore';
import LogItem from './LogItem';
import ReactDiffViewer from 'react-diff-viewer-continued';
import './DebugDrawer.css';

const DebugDrawer: React.FC = () => {
  const { history, currentIterationIndex, isDrawerOpen } = useStore();

  if (!isDrawerOpen || !history || history.length === 0) return null;

  const current = history[currentIterationIndex];
  const previous = currentIterationIndex > 0 ? history[currentIterationIndex - 1] : null;

  return (
    <div className="debug-drawer">
      <div className="drawer-section logs-section">
        <h3 className="section-title">Audit Logs (Iteration {currentIterationIndex})</h3>
        <div className="logs-list">
          {current.vqa_results.issues.length > 0 ? (
            current.vqa_results.issues.map((issue, idx) => (
              <LogItem key={idx} id={`issue-${currentIterationIndex}-${idx}`} issue={issue} />
            ))
          ) : (
            <div className="no-issues">No issues identified by VLM.</div>
          )}
        </div>
        {current.thoughts && (
          <div className="agent-thoughts">
            <h4>Agent Thoughts</h4>
            <p>{current.thoughts}</p>
          </div>
        )}
      </div>
      
      <div className="drawer-section diff-section">
        <h3 className="section-title">Code Changes</h3>
        <div className="diff-viewer-container">
          <ReactDiffViewer
            oldValue={previous?.svg_code || ''}
            newValue={current.svg_code}
            splitView={false}
            useDarkTheme={false}
            leftTitle={previous ? `Iteration ${currentIterationIndex - 1}` : 'None'}
            rightTitle={`Iteration ${currentIterationIndex}`}
            styles={{
              variables: {
                light: {
                  diffViewerBackground: '#fff',
                  addedBackground: '#e6ffec',
                  addedColor: '#24292e',
                  removedBackground: '#ffeef0',
                  removedColor: '#24292e',
                  wordAddedBackground: '#acf2bd',
                  wordRemovedBackground: '#fdb8c0',
                },
              },
              contentText: {
                fontSize: '12px',
                lineHeight: '1.4',
                fontFamily: 'Roboto Mono, monospace',
              },
            }}
          />
        </div>
      </div>
    </div>
  );
};

export default DebugDrawer;
