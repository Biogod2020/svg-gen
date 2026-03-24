import { describe, it, expect } from 'vitest';
import { calculateFitToScreen } from './scalingUtils';

describe('calculateFitToScreen', () => {
  it('returns scale 1 and center if content is smaller than container', () => {
    const container = { width: 1000, height: 800 };
    const content = { width: 500, height: 400 };
    const result = calculateFitToScreen(container, content);
    expect(result.scale).toBe(1);
    expect(result.x).toBe(0);
    expect(result.y).toBe(0);
  });

  it('scales down if content is wider than container', () => {
    const container = { width: 1000, height: 800 };
    const content = { width: 2000, height: 400 };
    const padding = 40;
    const result = calculateFitToScreen(container, content, padding);
    
    const expectedScale = (1000 - padding * 2) / 2000;
    expect(result.scale).toBe(expectedScale);
    expect(result.scale).toBeLessThan(1);
  });

  it('scales down if content is taller than container', () => {
    const container = { width: 1000, height: 800 };
    const content = { width: 500, height: 1600 };
    const padding = 40;
    const result = calculateFitToScreen(container, content, padding);
    
    const expectedScale = (800 - padding * 2) / 1600;
    expect(result.scale).toBe(expectedScale);
    expect(result.scale).toBeLessThan(1);
  });

  it('uses the smaller scale factor to ensure it fits both dimensions', () => {
    const container = { width: 1000, height: 1000 };
    const content = { width: 2000, height: 4000 };
    const padding = 0;
    const result = calculateFitToScreen(container, content, padding);
    
    expect(result.scale).toBe(0.25); // 1000/4000 is smaller than 1000/2000
  });

  it('handles zero dimensions gracefully', () => {
    const container = { width: 0, height: 0 };
    const content = { width: 100, height: 100 };
    const result = calculateFitToScreen(container, content);
    expect(result.scale).toBe(1);
  });
});
