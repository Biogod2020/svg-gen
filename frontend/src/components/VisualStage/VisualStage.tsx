import React, { useCallback } from 'react';
import { useSpring, animated } from '@react-spring/web';
import { useGesture } from '@use-gesture/react';
import { useStore } from '../../store/useStore';
import HotspotOverlay from './HotspotOverlay';
import ComparisonLayer from './ComparisonLayer';
import { ZoomIn, ZoomOut, Maximize } from 'lucide-react';
import './VisualStage.css';

const VisualStage: React.FC = () => {
  const { history, currentIterationIndex, comparisonMode } = useStore();
  const currentIteration = history[currentIterationIndex];

  const [style, api] = useSpring(() => ({
    x: 0,
    y: 0,
    scale: 1,
  }));

  const bind = useGesture(
    {
      onDrag: ({ offset: [x, y] }) => {
        api.start({ x, y });
      },
      onPinch: ({ offset: [d] }) => {
        api.start({ scale: d });
      },
      onWheel: ({ event, offset: [, y] }) => {
        if (event.ctrlKey) {
          // Zoom
          const newScale = Math.exp(-y / 200);
          api.start({ scale: newScale });
        } else {
          // Pan
          api.start({
            x: style.x.get() - event.deltaX,
            y: style.y.get() - event.deltaY,
          });
        }
      },
    },
    {
      drag: { from: () => [style.x.get(), style.y.get()] },
      pinch: { from: () => [style.scale.get(), 0] },
    }
  );

  const handleZoomIn = () => {
    api.start({ scale: style.scale.get() * 1.2 });
  };

  const handleZoomOut = () => {
    api.start({ scale: style.scale.get() / 1.2 });
  };

  const handleReset = () => {
    api.start({ x: 0, y: 0, scale: 1 });
  };

  if (!currentIteration) {
    return <div className="visual-stage-empty">No iteration selected</div>;
  }

  return (
    <div className="visual-stage-container" {...bind()}>
      <div className="visual-stage-controls">
        <button onClick={handleZoomIn} title="Zoom In"><ZoomIn size={20} /></button>
        <button onClick={handleZoomOut} title="Zoom Out"><ZoomOut size={20} /></button>
        <button onClick={handleReset} title="Reset View"><Maximize size={20} /></button>
      </div>

      <animated.div style={style} className="visual-stage-viewport">
        {comparisonMode === 'none' ? (
          <div className="svg-wrapper">
             <div 
              dangerouslySetInnerHTML={{ __html: currentIteration.svg_code }} 
              className="svg-content"
            />
            <HotspotOverlay issues={currentIteration.vqa_results.issues} />
          </div>
        ) : (
          <ComparisonLayer />
        )}
      </animated.div>
    </div>
  );
};

export default VisualStage;
