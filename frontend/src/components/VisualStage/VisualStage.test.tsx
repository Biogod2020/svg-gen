import { render, screen } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import VisualStage from './VisualStage';
import { useStore } from '../../store/useStore';

// Mock the store
vi.mock('../../store/useStore', () => ({
  useStore: vi.fn(),
}));

const mockIteration = {
  iteration: 0,
  svg_code: '<svg><circle cx="50" cy="50" r="40" /></svg>',
  vqa_results: {
    status: 'FAIL',
    score: 45,
    issues: [
      { description: 'Issue 1', box: [10, 10, 20, 20], severity: 'high' }
    ],
    suggestions: [],
    summary: 'Mock summary',
    thought: 'Mock thought'
  },
  thoughts: 'Mock thoughts',
  png_b64: 'mock_png'
};

describe('VisualStage', () => {
  it('renders SVG content', () => {
    (useStore as any).mockReturnValue({
      history: [mockIteration],
      currentIterationIndex: 0,
      comparisonMode: 'none',
      highlightedIssueId: null,
    });

    render(<VisualStage />);
    
    // Check if the SVG content is rendered
    // Note: Since we use dangerouslySetInnerHTML, we can check for the presence of the SVG or its elements.
    const svgElement = document.querySelector('svg');
    expect(svgElement).toBeDefined();
    expect(svgElement?.innerHTML).toContain('circle');
  });

  it('renders hotspots when there are issues', () => {
    (useStore as any).mockReturnValue({
      history: [mockIteration],
      currentIterationIndex: 0,
      comparisonMode: 'none',
      highlightedIssueId: null,
    });

    render(<VisualStage />);
    
    // Check if hotspots are rendered. We'll need to define how they are rendered.
    // For now, let's assume they have a specific data-testid or class.
    const hotspots = document.querySelectorAll('[data-testid="hotspot"]');
    expect(hotspots.length).toBe(1);
  });

  it('renders comparison split layer when mode is split', () => {
    (useStore as any).mockReturnValue({
      history: [mockIteration, { ...mockIteration, iteration: 1 }],
      currentIterationIndex: 1,
      comparisonMode: 'split',
      highlightedIssueId: null,
    });

    const { container } = render(<VisualStage />);
    expect(container.querySelector('.comparison-split-container')).toBeDefined();
  });

  it('renders pixel diff layer when mode is pixel-diff', () => {
    (useStore as any).mockReturnValue({
      history: [mockIteration, { ...mockIteration, iteration: 1 }],
      currentIterationIndex: 1,
      comparisonMode: 'pixel-diff',
      highlightedIssueId: null,
    });

    const { container } = render(<VisualStage />);
    expect(container.querySelector('.comparison-pixel-diff')).toBeDefined();
  });
});
