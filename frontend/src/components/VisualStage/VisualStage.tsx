import React, { useCallback, useRef, useLayoutEffect, useEffect } from 'react';
import { useSpring, animated } from '@react-spring/web';
import { useGesture } from '@use-gesture/react';
import { useStore } from '../../store/useStore';
import HotspotOverlay from './HotspotOverlay';
import ComparisonLayer from './ComparisonLayer';
import { ZoomIn, ZoomOut, Maximize } from 'lucide-react';
import { calculateFitToScreen } from './scalingUtils';
import './VisualStage.css';

const VisualStage: React.FC = () => {
  const { history, currentIterationIndex, comparisonMode } = useStore();
  const currentIteration = history[currentIterationIndex];
  const containerRef = useRef<HTMLDivElement>(null);
  const contentRef = useRef<HTMLDivElement>(null);
  const lastIterationRef = useRef<number | null>(null);

  const [style, api] = useSpring(() => ({
    x: 0,
    y: 0,
    scale: 1,
  }));

  const handleFitToScreen = useCallback(() => {
    if (containerRef.current && contentRef.current) {
      const containerBounds = containerRef.current.getBoundingClientRect();
      const svg = contentRef.current.querySelector('svg');
      const img = contentRef.current.querySelector('img');
      
      let contentWidth = 0;
      let contentHeight = 0;

      if (svg) {
        // Use viewBox if available for intrinsic dimensions
        if (svg.viewBox && svg.viewBox.baseVal && svg.viewBox.baseVal.width > 0) {
          contentWidth = svg.viewBox.baseVal.width;
          contentHeight = svg.viewBox.baseVal.height;
        } else if (svg.width && svg.width.baseVal && svg.width.baseVal.value > 0) {
          contentWidth = svg.width.baseVal.value;
          contentHeight = svg.height.baseVal.value;
        } else {
          // Fallback to getBBox() which is unscaled in SVG coordinate system
          try {
            const bbox = svg.getBBox();
            contentWidth = bbox.width;
            contentHeight = bbox.height;
          } catch (e) {
            // Fallback for elements not yet in DOM or other issues
            const currentScale = style.scale.get();
            contentWidth = (svg as any).offsetWidth / (currentScale || 1);
            contentHeight = (svg as any).offsetHeight / (currentScale || 1);
          }
        }
      } else if (img) {
        contentWidth = img.naturalWidth || img.width;
        contentHeight = img.naturalHeight || img.height;
      }

      if (contentWidth > 0 && contentHeight > 0) {
        const { scale, x, y } = calculateFitToScreen(
          { width: containerBounds.width, height: containerBounds.height },
          { width: contentWidth, height: contentHeight },
          100 // Increased padding for breathing room
        );

        api.start({ x, y, scale, immediate: false });
      }
    }
  }, [api, style.scale]);

  // Handle auto-fit when new iteration arrives or mode changes
  useLayoutEffect(() => {
    if (currentIteration) {
      // Small delay to ensure the SVG is rendered and measurable
      const timer = setTimeout(() => {
        handleFitToScreen();
        lastIterationRef.current = currentIterationIndex;
      }, 0);
      return () => clearTimeout(timer);
    }
  }, [currentIterationIndex, currentIteration, comparisonMode, handleFitToScreen]);

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

  if (!currentIteration) {
    return <div className="visual-stage-empty">No iteration selected</div>;
  }

  return (
    <div ref={containerRef} className="visual-stage-container" {...bind()}>
      <div className="visual-stage-controls">
        <button onClick={handleZoomIn} title="Zoom In"><ZoomIn size={20} /></button>
        <button onClick={handleZoomOut} title="Zoom Out"><ZoomOut size={20} /></button>
        <button onClick={handleFitToScreen} title="Fit to Screen"><Maximize size={20} /></button>
      </div>

      <animated.div style={style} className="visual-stage-viewport">
        {comparisonMode === 'none' ? (
          <div ref={contentRef} className="svg-wrapper">
             <div 
              dangerouslySetInnerHTML={{ __html: currentIteration.svg_code }} 
              className="svg-content"
            />
            {/* Hotspots hidden in customer-facing mode */}
          </div>
        ) : (
          <div ref={contentRef}>
            <ComparisonLayer />
          </div>
        )}
      </animated.div>
    </div>
  );
};

export default VisualStage;
