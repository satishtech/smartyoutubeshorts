// Pure drag/resize math for the Timeline component, kept in its own module
// (rather than exported from Timeline.tsx) so the file stays component-only
// for Fast Refresh, and so this logic is trivially unit-testable.

export const MIN_SEGMENT_SECONDS = 1;
export const MAX_SEGMENT_SECONDS = 60; // Domain rule: every Short <= 60s.

export type DragEdge = 'start' | 'end';

export interface SegmentBounds {
  start_time: number;
  end_time: number;
}

/**
 * Given which edge is being dragged and a proposed time (in seconds),
 * return the new start/end for the segment, clamped so that:
 *  - it never goes outside [0, durationSeconds]
 *  - it's never shorter than MIN_SEGMENT_SECONDS
 *  - it's never longer than MAX_SEGMENT_SECONDS (Short domain rule)
 */
export function resizeSegment(
  edge: DragEdge,
  proposedTime: number,
  segment: SegmentBounds,
  durationSeconds: number
): SegmentBounds {
  const clampedTime = Math.min(Math.max(proposedTime, 0), durationSeconds);

  if (edge === 'start') {
    const maxStart = segment.end_time - MIN_SEGMENT_SECONDS;
    const minStart = Math.max(0, segment.end_time - MAX_SEGMENT_SECONDS);
    const start_time = Math.min(Math.max(clampedTime, minStart), maxStart);
    return { start_time, end_time: segment.end_time };
  }

  const minEnd = segment.start_time + MIN_SEGMENT_SECONDS;
  const maxEnd = Math.min(durationSeconds, segment.start_time + MAX_SEGMENT_SECONDS);
  const end_time = Math.min(Math.max(clampedTime, minEnd), maxEnd);
  return { start_time: segment.start_time, end_time };
}

/** Convert a pointer x position within the track into a time in seconds. */
export function pixelToTime(offsetX: number, trackWidth: number, durationSeconds: number): number {
  if (trackWidth <= 0) return 0;
  const ratio = Math.min(Math.max(offsetX / trackWidth, 0), 1);
  return ratio * durationSeconds;
}
