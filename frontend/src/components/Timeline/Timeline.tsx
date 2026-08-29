import { useCallback, useEffect, useRef, useState } from 'react';
import { motion } from 'framer-motion';
import { cn, formatDuration } from '../../lib/utils';
import { pixelToTime, resizeSegment, type DragEdge } from './timelineMath';
import type { HighlightSegment } from '../../types';

interface TimelineProps {
  durationSeconds: number;
  highlights: HighlightSegment[];
  onUpdate: (highlightId: number, payload: { start_time: number; end_time: number }) => Promise<void>;
  onRemove: (highlightId: number) => Promise<void>;
}

interface DragState {
  highlightId: number;
  edge: DragEdge;
}

export function Timeline({ durationSeconds, highlights, onUpdate, onRemove }: TimelineProps) {
  const trackRef = useRef<HTMLDivElement>(null);
  const [dragHighlightId, setDragHighlightId] = useState<number | null>(null);
  const [liveSegments, setLiveSegments] = useState<Record<number, { start_time: number; end_time: number }>>({});
  const [removingId, setRemovingId] = useState<number | null>(null);

  const safeDuration = durationSeconds > 0 ? durationSeconds : 1;

  // Refs mirror the latest render's values so the window-level pointer
  // listeners (attached once per drag) never see a stale closure.
  const dragStateRef = useRef<DragState | null>(null);
  const highlightsRef = useRef(highlights);
  highlightsRef.current = highlights;
  const liveSegmentsRef = useRef(liveSegments);
  liveSegmentsRef.current = liveSegments;
  const safeDurationRef = useRef(safeDuration);
  safeDurationRef.current = safeDuration;
  const onUpdateRef = useRef(onUpdate);
  onUpdateRef.current = onUpdate;

  const getSegmentValues = (segment: HighlightSegment) => liveSegments[segment.id] ?? segment;

  const onPointerMove = useCallback((event: PointerEvent) => {
    const dragState = dragStateRef.current;
    if (!dragState || !trackRef.current) return;
    const rect = trackRef.current.getBoundingClientRect();
    const offsetX = event.clientX - rect.left;
    const time = pixelToTime(offsetX, rect.width, safeDurationRef.current);

    const segment = highlightsRef.current.find((h) => h.id === dragState.highlightId);
    if (!segment) return;
    const base = liveSegmentsRef.current[segment.id] ?? segment;
    const next = resizeSegment(dragState.edge, time, base, safeDurationRef.current);
    setLiveSegments((current) => ({ ...current, [segment.id]: next }));
  }, []);

  const onPointerUp = useCallback(() => {
    const dragState = dragStateRef.current;
    dragStateRef.current = null;
    setDragHighlightId(null);
    window.removeEventListener('pointermove', onPointerMove);

    if (!dragState) return;
    const finalValues = liveSegmentsRef.current[dragState.highlightId];
    if (finalValues) {
      void onUpdateRef.current(dragState.highlightId, finalValues).catch(() => {
        // onUpdate is responsible for surfacing/rolling back errors.
      });
    }
  }, [onPointerMove]);

  useEffect(() => {
    // Safety net: release listeners if the component unmounts mid-drag.
    return () => {
      window.removeEventListener('pointermove', onPointerMove);
      window.removeEventListener('pointerup', onPointerUp);
    };
  }, [onPointerMove, onPointerUp]);

  const startDrag = (highlightId: number, edge: DragEdge) => {
    dragStateRef.current = { highlightId, edge };
    setDragHighlightId(highlightId);
    window.addEventListener('pointermove', onPointerMove);
    window.addEventListener('pointerup', onPointerUp, { once: true });
  };

  const handleRemove = async (highlightId: number) => {
    setRemovingId(highlightId);
    try {
      await onRemove(highlightId);
    } finally {
      setRemovingId(null);
    }
  };

  return (
    <div className="w-full">
      <div className="mb-3 flex justify-between text-xs text-gray-500">
        <span>0:00</span>
        <span>{formatDuration(durationSeconds)}</span>
      </div>

      <div
        ref={trackRef}
        data-testid="timeline-track"
        className="relative h-16 w-full rounded-xl border border-white/10 bg-white/[0.03]"
      >
        {/* Center scrub line, matching the diamond-marker reference look */}
        <div className="absolute left-0 right-0 top-1/2 h-px -translate-y-1/2 bg-white/10" aria-hidden="true" />

        {highlights.map((segment) => {
          const values = getSegmentValues(segment);
          const leftPct = (values.start_time / safeDuration) * 100;
          const widthPct = ((values.end_time - values.start_time) / safeDuration) * 100;

          return (
            <motion.div
              key={segment.id}
              data-testid={`segment-${segment.id}`}
              initial={{ opacity: 0 }}
              animate={{ opacity: removingId === segment.id ? 0.4 : 1 }}
              className={cn(
                'absolute top-1/2 h-8 -translate-y-1/2 rounded-full bg-gradient-to-r from-violet-500/80 to-pink-500/80 shadow-md shadow-pink-500/20',
                dragHighlightId === segment.id && 'ring-2 ring-pink-300'
              )}
              style={{ left: `${leftPct}%`, width: `${Math.max(widthPct, 1)}%` }}
            >
              {/* Diamond marker: start */}
              <span
                aria-hidden="true"
                className="pointer-events-none absolute left-0 top-1/2 h-3 w-3 -translate-x-1/2 -translate-y-1/2 rotate-45 rounded-[2px] bg-white shadow"
              />
              <button
                type="button"
                aria-label={`Adjust start time of ${segment.title}`}
                data-testid={`handle-start-${segment.id}`}
                onPointerDown={() => startDrag(segment.id, 'start')}
                className="absolute -left-2 top-0 h-full w-4 cursor-ew-resize"
              />
              <div className="flex h-full items-center justify-between overflow-hidden px-4 text-xs font-medium text-white">
                <span className="truncate">{segment.title}</span>
                <button
                  type="button"
                  aria-label={`Remove ${segment.title}`}
                  onClick={() => void handleRemove(segment.id)}
                  disabled={removingId === segment.id}
                  className="ml-2 shrink-0 rounded-full bg-black/30 px-1.5 py-0.5 hover:bg-black/50"
                >
                  &times;
                </button>
              </div>
              <button
                type="button"
                aria-label={`Adjust end time of ${segment.title}`}
                data-testid={`handle-end-${segment.id}`}
                onPointerDown={() => startDrag(segment.id, 'end')}
                className="absolute -right-2 top-0 h-full w-4 cursor-ew-resize"
              />
              {/* Diamond marker: end */}
              <span
                aria-hidden="true"
                className="pointer-events-none absolute right-0 top-1/2 h-3 w-3 translate-x-1/2 -translate-y-1/2 rotate-45 rounded-[2px] bg-white shadow"
              />
            </motion.div>
          );
        })}
      </div>

      <ul className="mt-4 flex flex-col gap-2">
        {highlights.map((segment) => {
          const values = getSegmentValues(segment);
          return (
            <li
              key={segment.id}
              className={cn(
                'flex items-center justify-between rounded-lg border border-white/10 bg-white/[0.02] px-3 py-2 text-sm'
              )}
            >
              <span className="font-medium text-gray-700">{segment.title}</span>
              <span className="text-gray-500">
                {formatDuration(values.start_time)} – {formatDuration(values.end_time)}
              </span>
            </li>
          );
        })}
      </ul>
    </div>
  );
}
