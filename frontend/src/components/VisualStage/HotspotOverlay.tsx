import React from 'react';
import { useStore } from "../../store/useStore";
import type { AuditIssue } from "../../types";

import './HotspotOverlay.css';

interface HotspotOverlayProps {
  issues: AuditIssue[];
}

const HotspotOverlay: React.FC<HotspotOverlayProps> = ({ issues }) => {
  const { currentIterationIndex, highlightedIssueId, setHighlightedIssue } = useStore();

  return (
    <div className="hotspot-overlay">
      {issues.map((issue, idx) => {
        if (!issue.box) return null;
        
        const id = `issue-${currentIterationIndex}-${idx}`;
        const [ymin, xmin, ymax, xmax] = issue.box;
        const isHighlighted = highlightedIssueId === id;

        return (
          <div
            key={id}
            className={`hotspot ${issue.severity} ${isHighlighted ? 'highlighted' : ''}`}
            style={{
              top: `${ymin / 10}%`,
              left: `${xmin / 10}%`,
              width: `${(xmax - xmin) / 10}%`,
              height: `${(ymax - ymin) / 10}%`,
            }}
            onClick={(e) => {
              e.stopPropagation();
              setHighlightedIssue(isHighlighted ? null : id);
            }}
          >
            <div className="hotspot-pulse" />
          </div>
        );
      })}
    </div>
  );
};

export default HotspotOverlay;
