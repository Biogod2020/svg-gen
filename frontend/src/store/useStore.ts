import { create } from 'zustand';
import { AppState, ComparisonMode, Iteration } from '../types';

export const useStore = create<AppState>((set) => ({
  history: [],
  currentIterationIndex: 0,
  highlightedIssueId: null,
  isDrawerOpen: true,
  comparisonMode: 'none',

  setHistory: (history: Iteration[]) => set({ history }),
  
  setCurrentIteration: (index: number) => set({ currentIterationIndex: index }),
  
  setHighlightedIssue: (id: string | null) => set({ highlightedIssueId: id }),
  
  toggleDrawer: () => set((state) => ({ isDrawerOpen: !state.isDrawerOpen })),
  
  setComparisonMode: (mode: ComparisonMode) => set({ comparisonMode: mode }),
}));
