import { describe, it, expect, beforeEach, vi } from 'vitest';
import { useStore } from '../useStore';

describe('useStore streaming', () => {
  beforeEach(() => {
    useStore.setState({
      history: [],
      currentIterationIndex: 0,
      highlightedIssueId: null,
      isDrawerOpen: true,
      comparisonMode: 'none'
    });
    vi.stubGlobal('fetch', vi.fn());
  });

  it('should process streaming iterations and append to history', async () => {
    const mockStream = new ReadableStream({
      start(controller) {
        const encoder = new TextEncoder();
        const iterations = [
          {
            iteration: 1,
            svg_code: '<svg>1</svg>',
            thoughts: 'Thought 1',
            vqa_results: { status: 'FAIL', score: 50, issues: [], suggestions: [], summary: 'S1' }
          },
          {
            iteration: 2,
            svg_code: '<svg>2</svg>',
            thoughts: 'Thought 2',
            vqa_results: { status: 'PASS', score: 90, issues: [], suggestions: [], summary: 'S2' }
          }
        ];

        iterations.forEach((it) => {
          controller.enqueue(encoder.encode(`data: ${JSON.stringify(it)}\n\n`));
        });
        controller.enqueue(encoder.encode('data: [DONE]\n\n'));
        controller.close();
      }
    });

    vi.mocked(fetch).mockResolvedValue({
      ok: true,
      body: mockStream
    } as Response);

    const { generateStream } = useStore.getState();
    
    await generateStream('test prompt', ['minimalist']);

    const state = useStore.getState();
    expect(state.history).toHaveLength(2);
    expect(state.history[0].iteration).toBe(1);
    expect(state.history[1].iteration).toBe(2);
    expect(state.currentIterationIndex).toBe(1); // Should point to the last iteration (0-indexed)
  });
});
