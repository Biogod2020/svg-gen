import { create } from 'zustand';
import type { AppState, ComparisonMode, Iteration } from '../types';

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

  generateStream: async (prompt: string, style_hints: string[]) => {
    try {
      const response = await fetch('/generate-stream', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ prompt, style_hints }),
      });

      if (!response.ok || !response.body) {
        throw new Error('Failed to start generation stream');
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = '';

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        
        const lines = buffer.split('\n');
        buffer = lines.pop() || ''; // Keep the last partial line in buffer

        for (const line of lines) {
          if (!line.startsWith('data: ')) continue;
          
          const data = line.slice(6).trim();
          if (data === '[DONE]') break;

          try {
            const iteration: Iteration = JSON.parse(data);
            set((state) => {
              // Find if iteration already exists to update it (upsert)
              const existingIndex = state.history.findIndex(it => it.iteration === iteration.iteration);
              let newHistory;
              
              if (existingIndex >= 0) {
                newHistory = [...state.history];
                newHistory[existingIndex] = iteration;
              } else {
                newHistory = [...state.history, iteration];
              }

              return {
                history: newHistory,
                currentIterationIndex: newHistory.length - 1,
              };
            });
          } catch (e) {
            console.error('Error parsing streaming iteration:', e);
          }
        }
      }
    } catch (error) {
      console.error('Streaming error:', error);
    }
  },
}));
