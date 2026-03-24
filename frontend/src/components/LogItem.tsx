import React from 'react';
import type { AuditIssue } from '../types';
import { useStore } from '../store/useStore';
import { AlertCircle, AlertTriangle, Info } from 'lucide-react';
import './LogItem.css';

interface LogItemProps {
  issue: AuditIssue;
  id: string;
}

const LogItem: React.FC<LogItemProps> = ({ issue, id }) => {
  const { highlightedIssueId, setHighlightedIssue } = useStore();
  const isHighlighted = highlightedIssueId === id;

  const getIcon = () => {
    switch (issue.severity) {
      case 'high': return <AlertCircle className="issue-icon high" size={18} />;
      case 'medium': return <AlertTriangle className="issue-icon medium" size={18} />;
      default: return <Info className="issue-icon low" size={18} />;
    }
  };

  return (
    <div 
      className={`log-item ${issue.severity} ${isHighlighted ? 'highlighted' : ''}`}
      onClick={() => setHighlightedIssue(isHighlighted ? null : id)}
    >
      <div className="log-item-header">
        {getIcon()}
        <span className="log-item-severity">{issue.severity.toUpperCase()}</span>
      </div>
      <div className="log-item-body">
        <p className="log-item-description">{issue.description}</p>
        {issue.box && (
          <span className="log-item-box-tag">
            Spatial Data: [{issue.box.map(b => Math.round(b)).join(', ')}]
          </span>
        )}
      </div>
    </div>
  );
};

export default LogItem;
