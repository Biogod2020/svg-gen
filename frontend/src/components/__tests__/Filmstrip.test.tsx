import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import React from 'react';
import Filmstrip from '../Filmstrip';
import { useStore } from '../../store/useStore';

// Mock the store
vi.mock('../../store/useStore', () => ({
  useStore: vi.fn(),
}));

const mockHistory = [
  {
    iteration: 0,
    svg_code: '<svg>0</svg>',
    vqa_results: { status: 'FAIL', score: 50, issues: [], suggestions: [], summary: '' },
    thoughts: 'Initial',
  },
  {
    iteration: 1,
    svg_code: '<svg>1</svg>',
    vqa_results: { status: 'PASS', score: 100, issues: [], suggestions: [], summary: '' },
    thoughts: 'Fixed',
  },
];

describe('Filmstrip Component', () => {
  const setCurrentIteration = vi.fn();
  const setComparisonMode = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
    (useStore as any).mockReturnValue({
      history: mockHistory,
      currentIterationIndex: 0,
      setCurrentIteration,
      comparisonMode: 'none',
      setComparisonMode,
    });
  });

  it('renders all iterations as thumbnails', () => {
    render(<Filmstrip />);
    expect(screen.getByTestId('thumbnail-0')).toBeDefined();
    expect(screen.getByTestId('thumbnail-1')).toBeDefined();
    expect(screen.getByText('Iter 0')).toBeDefined();
    expect(screen.getByText('Iter 1')).toBeDefined();
  });

  it('highlights the current iteration', () => {
    render(<Filmstrip />);
    const thumbnail0 = screen.getByTestId('thumbnail-0');
    expect(thumbnail0.className).toContain('active');
  });

  it('calls setCurrentIteration when a thumbnail is clicked', () => {
    render(<Filmstrip />);
    const thumbnail1 = screen.getByTestId('thumbnail-1');
    fireEvent.click(thumbnail1);
    expect(setCurrentIteration).toHaveBeenCalledWith(1);
  });

  it('toggles comparison mode when compare button is clicked', () => {
    render(<Filmstrip />);
    const compareBtn = screen.getByText('Compare');
    fireEvent.click(compareBtn);
    expect(setComparisonMode).toHaveBeenCalledWith('split');
  });

  it('shows correct status icons', () => {
    const { container } = render(<Filmstrip />);
    const passIcon = container.querySelector('.status-icon.pass');
    const failIcon = container.querySelector('.status-icon.fail');
    expect(passIcon).toBeDefined();
    expect(failIcon).toBeDefined();
  });
});
