import { describe, it, expect, beforeEach } from 'vitest';
import { useStore } from '../useStore';
import { Iteration } from '../../types';

const mockIteration: Iteration = {
  iteration: 0,
  svg_code: '<svg></svg>',
  thoughts: 'Initial version',
  vqa_results: {
    status: 'FAIL',
    score: 45,
    issues: [
      { description: 'Poor contrast', box: [10, 10, 100, 100], severity: 'high' }
    ],
    suggestions: ['Increase contrast'],
    summary: 'Needs improvement'
  }
};

describe('useStore', () => {
  beforeEach(() => {
    // Reset the store to initial state
    useStore.setState({
      history: [],
      currentIterationIndex: 0,
      highlightedIssueId: null,
      isDrawerOpen: true,
      comparisonMode: 'none'
    });
  });

  it('should have initial state', () => {
    const state = useStore.getState();
    expect(state.history).toEqual([]);
    expect(state.currentIterationIndex).toBe(0);
    expect(state.highlightedIssueId).toBeNull();
    expect(state.isDrawerOpen).toBe(true);
    expect(state.comparisonMode).toBe('none');
  });

  it('should set history', () => {
    const { setHistory } = useStore.getState();
    const history = [mockIteration];
    setHistory(history);
    expect(useStore.getState().history).toEqual(history);
  });

  it('should set current iteration', () => {
    const { setCurrentIteration } = useStore.getState();
    setCurrentIteration(1);
    expect(useStore.getState().currentIterationIndex).toBe(1);
  });

  it('should set highlighted issue', () => {
    const { setHighlightedIssue } = useStore.getState();
    setHighlightedIssue('issue-1');
    expect(useStore.getState().highlightedIssueId).toBe('issue-1');
  });

  it('should toggle drawer', () => {
    const { toggleDrawer } = useStore.getState();
    toggleDrawer();
    expect(useStore.getState().isDrawerOpen).toBe(false);
    toggleDrawer();
    expect(useStore.getState().isDrawerOpen).toBe(true);
  });

  it('should set comparison mode', () => {
    const { setComparisonMode } = useStore.getState();
    setComparisonMode('split');
    expect(useStore.getState().comparisonMode).toBe('split');
  });
});
