export interface AuditIssue {
  description: string;
  box: number[] | null;
  severity: 'low' | 'medium' | 'high';
}

export interface AuditResult {
  status: 'PENDING' | 'PASS' | 'FAIL' | 'SKIPPED';
  score: number;
  issues: AuditIssue[];
  suggestions: string[];
  summary: string;
  thought?: string;
}

export interface Iteration {
  iteration: number;
  svg_code: string;
  vqa_results: AuditResult;
  thoughts: string;
  png_b64?: string;
}

export type ComparisonMode = 'none' | 'split' | 'pixel-diff';

export interface AppState {
  history: Iteration[];
  currentIterationIndex: number;
  highlightedIssueId: string | null;
  isDrawerOpen: boolean;
  comparisonMode: ComparisonMode;
  
  // Actions
  setHistory: (history: Iteration[]) => void;
  setCurrentIteration: (index: number) => void;
  setHighlightedIssue: (id: string | null) => void;
  toggleDrawer: () => void;
  setComparisonMode: (mode: ComparisonMode) => void;
  generateStream: (prompt: string, style_hints: string[]) => Promise<void>;
}
