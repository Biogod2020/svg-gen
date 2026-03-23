import React from 'react';
import { useStore } from '../../store/useStore';
import { AuditIssue } from '../../types';
import './HotspotOverlay.css';

interface HotspotOverlayProps {
  issues: AuditIssue[];
}

const HotspotOverlay: React.FC<HotspotOverlayProps> = ({ issues }) => {
  const { setHighlightedIssue, highlightedIssueId } = useStore();

  return (
    <div className="hotspot-overlay">
      {issues.map((issue, index) => {
        if (!issue.box || issue.box.length !== 4) return null;
        
        const [ymin, xmin, ymax, xmax] = issue.box;
        const left = `${xmin * 100}%`;
        const top = `${ymin * 100}%`;
        const width = `${(xmax - xmin) * 100}%`;
        const height = `${(ymax - ymin) * 100}%`;
        const issueId = `issue-${index}`;

        return (
          <div
            key={issueId}
            data-testid="hotspot"
            className={`hotspot ${issue.severity} ${highlightedIssueId === issueId ? 'active' : ''}`}
            style={{ left, top, width, height }}
            onClick={() => setHighlightedIssue(issueId)}
          >
            <div className="hotspot-pulse" />
          </div>
        );
      })}
    </div>
  );
};

export default HotspotOverlay;
