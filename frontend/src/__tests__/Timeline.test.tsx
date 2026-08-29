import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, expect, test, vi } from 'vitest';
import { Timeline } from '../components/Timeline/Timeline';
import {
  MAX_SEGMENT_SECONDS,
  MIN_SEGMENT_SECONDS,
  pixelToTime,
  resizeSegment,
} from '../components/Timeline/timelineMath';
import type { HighlightSegment } from '../types';

describe('resizeSegment (drag-adjust logic)', () => {
  const base = { start_time: 10, end_time: 20 };

  test('moves the start edge to the proposed time', () => {
    const result = resizeSegment('start', 5, base, 120);
    expect(result).toEqual({ start_time: 5, end_time: 20 });
  });

  test('moves the end edge to the proposed time', () => {
    const result = resizeSegment('end', 30, base, 120);
    expect(result).toEqual({ start_time: 10, end_time: 30 });
  });

  test('clamps the start edge so the segment never drops below the minimum duration', () => {
    const result = resizeSegment('start', 19.9, base, 120);
    expect(result.end_time - result.start_time).toBeGreaterThanOrEqual(MIN_SEGMENT_SECONDS);
  });

  test('clamps the end edge so the segment never exceeds the 60s domain rule', () => {
    const result = resizeSegment('end', 1000, { start_time: 0, end_time: 10 }, 5000);
    expect(result.end_time - result.start_time).toBeLessThanOrEqual(MAX_SEGMENT_SECONDS);
    expect(result.end_time).toBe(MAX_SEGMENT_SECONDS);
  });

  test('clamps proposed times to the video duration bounds', () => {
    const result = resizeSegment('end', 999, base, 25);
    expect(result.end_time).toBeLessThanOrEqual(25);
  });

  test('never lets the start edge go negative', () => {
    const result = resizeSegment('start', -50, base, 120);
    expect(result.start_time).toBeGreaterThanOrEqual(0);
  });
});

describe('pixelToTime', () => {
  test('maps a pixel offset proportionally onto the duration', () => {
    expect(pixelToTime(50, 100, 200)).toBe(100);
  });

  test('clamps negative offsets to 0', () => {
    expect(pixelToTime(-20, 100, 200)).toBe(0);
  });

  test('clamps offsets beyond the track width to the full duration', () => {
    expect(pixelToTime(500, 100, 200)).toBe(200);
  });

  test('returns 0 when the track has no measurable width', () => {
    expect(pixelToTime(50, 0, 200)).toBe(0);
  });
});

function makeHighlight(overrides: Partial<HighlightSegment> = {}): HighlightSegment {
  return {
    id: 1,
    project_id: 1,
    order: 0,
    start_time: 10,
    end_time: 20,
    title: 'Great moment',
    reason: 'High energy',
    score: 0.9,
    created_at: '2026-01-01T00:00:00Z',
    updated_at: '2026-01-01T00:00:00Z',
    ...overrides,
  };
}

describe('Timeline component', () => {
  test('renders one block per highlight segment with its label', () => {
    const highlights = [makeHighlight({ id: 1, title: 'Intro' }), makeHighlight({ id: 2, title: 'Outro', start_time: 30, end_time: 40 })];
    render(
      <Timeline
        durationSeconds={120}
        highlights={highlights}
        onUpdate={vi.fn().mockResolvedValue(undefined)}
        onRemove={vi.fn().mockResolvedValue(undefined)}
      />
    );
    expect(screen.getByTestId('segment-1')).toBeInTheDocument();
    expect(screen.getByTestId('segment-2')).toBeInTheDocument();
    expect(screen.getAllByText('Intro').length).toBeGreaterThan(0);
    expect(screen.getAllByText('Outro').length).toBeGreaterThan(0);
  });

  test('calls onRemove when the remove button on a segment is clicked', async () => {
    const onRemove = vi.fn().mockResolvedValue(undefined);
    const user = userEvent.setup();
    render(
      <Timeline
        durationSeconds={120}
        highlights={[makeHighlight({ id: 1, title: 'Intro' })]}
        onUpdate={vi.fn().mockResolvedValue(undefined)}
        onRemove={onRemove}
      />
    );

    await user.click(screen.getByRole('button', { name: /remove intro/i }));

    await waitFor(() => {
      expect(onRemove).toHaveBeenCalledWith(1);
    });
  });
});
