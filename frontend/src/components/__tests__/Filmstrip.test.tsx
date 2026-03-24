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
    const { container } = render(<Filmstrip />);
    const items = container.querySelectorAll('.filmstrip-item');
    expect(items.length).toBe(2);
    expect(screen.getAllByText('Initial').length).toBeGreaterThan(0);
    expect(screen.getByText('Repair 1')).toBeDefined();
  });

  it('highlights the current iteration', () => {
    const { container } = render(<Filmstrip />);
    const items = container.querySelectorAll('.filmstrip-item');
    expect(items[0].className).toContain('selected');
  });

  it('calls setCurrentIteration when a thumbnail is clicked', () => {
    const { container } = render(<Filmstrip />);
    const items = container.querySelectorAll('.filmstrip-item');
    fireEvent.click(items[1]);
    expect(setCurrentIteration).toHaveBeenCalledWith(1);
  });

  it('shows correct status icons', () => {
    const { container } = render(<Filmstrip />);
    const passIcon = container.querySelector('.status-badge.pass');
    const failIcon = container.querySelector('.status-badge.fail');
    expect(passIcon).toBeDefined();
    expect(failIcon).toBeDefined();
  });
});

