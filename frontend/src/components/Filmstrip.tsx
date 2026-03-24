import React from 'react';
import { useStore } from '../store/useStore';
import { CheckCircle2, XCircle, Clock } from 'lucide-react';
import './Filmstrip.css';

const Filmstrip: React.FC = () => {
  const { history, currentIterationIndex, setCurrentIteration } = useStore();

  if (!history || history.length === 0) {
    return <div className="filmstrip-empty">No iterations yet</div>;
  }

  return (
    <div className="filmstrip-container">
      {history.map((iteration, index) => {
        const isSelected = index === currentIterationIndex;
        const status = iteration.vqa_results.status;

        return (
          <div
            key={index}
            className={`filmstrip-item ${isSelected ? 'selected' : ''}`}
            onClick={() => setCurrentIteration(index)}
          >
            <div className="thumbnail-wrapper">
              {iteration.png_b64 ? (
                <img
                  src={`data:image/png;base64,${iteration.png_b64}`}
                  alt={`Iteration ${index}`}
                  className="thumbnail-img"
                />
              ) : (
                <div className="thumbnail-placeholder">
                  {iteration.iteration === 0 ? 'Initial' : `Rep ${iteration.iteration}`}
                </div>
              )}
              <div className={`status-badge ${status.toLowerCase()}`}>
                {status === 'PASS' && <CheckCircle2 size={14} />}
                {status === 'FAIL' && <XCircle size={14} />}
                {status === 'PENDING' && <Clock size={14} />}
              </div>
            </div>
            <div className="iteration-label">
              {index === 0 ? 'Initial' : `Repair ${index}`}
            </div>
          </div>
        );
      })}
    </div>
  );
};

export default Filmstrip;
