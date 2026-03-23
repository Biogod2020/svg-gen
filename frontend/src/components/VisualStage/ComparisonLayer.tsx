import React, { useState } from 'react';
import { useStore } from '../../store/useStore';
import './ComparisonLayer.css';

const ComparisonLayer: React.FC = () => {
  const { history, currentIterationIndex, comparisonMode } = useStore();
  const [sliderPos, setSliderPos] = useState(50);

  const current = history[currentIterationIndex];
  const previous = history[currentIterationIndex - 1] || history[0];

  if (!current || !previous) return null;

  const handleSliderChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setSliderPos(Number(e.target.value));
  };

  if (comparisonMode === 'split') {
    return (
      <div className="comparison-split-container">
        <div className="comparison-layer base">
          <div dangerouslySetInnerHTML={{ __html: previous.svg_code }} className="svg-content" />
        </div>
        <div 
          className="comparison-layer overlay" 
          style={{ clipPath: `inset(0 0 0 ${sliderPos}%)` }}
        >
          <div dangerouslySetInnerHTML={{ __html: current.svg_code }} className="svg-content" />
        </div>
        <div className="split-handle" style={{ left: `${sliderPos}%` }}>
           <input 
            type="range" 
            min="0" 
            max="100" 
            value={sliderPos} 
            onChange={handleSliderChange} 
            className="split-slider-input"
          />
        </div>
      </div>
    );
  }

  if (comparisonMode === 'pixel-diff') {
    return (
      <div className="comparison-pixel-diff">
        {previous.png_b64 && (
          <img 
            src={`data:image/png;base64,${previous.png_b64}`} 
            className="diff-image base" 
            alt="Previous"
          />
        )}
        {current.png_b64 && (
          <img 
            src={`data:image/png;base64,${current.png_b64}`} 
            className="diff-image overlay" 
            alt="Current"
          />
        )}
      </div>
    );
  }

  return null;
};

export default ComparisonLayer;
