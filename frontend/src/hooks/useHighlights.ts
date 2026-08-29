import { useCallback, useEffect, useState } from 'react';
import * as highlightService from '../services/highlightService';
import * as projectService from '../services/projectService';
import { getErrorMessage } from '../services/api';
import type { HighlightSegment, UpdateHighlightPayload } from '../types';

const DETECT_POLL_INTERVAL_MS = 2500;
const DETECT_POLL_MAX_ATTEMPTS = 40; // ~100s, generous for a Claude call

function sleep(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

interface UseHighlightsResult {
  highlights: HighlightSegment[];
  isLoading: boolean;
  isDetecting: boolean;
  error: string | null;
  refetch: () => Promise<void>;
  detect: (numShorts?: number) => Promise<void>;
  updateHighlight: (highlightId: number, payload: UpdateHighlightPayload) => Promise<void>;
  removeHighlight: (highlightId: number) => Promise<void>;
}

export function useHighlights(projectId: number): UseHighlightsResult {
  const [highlights, setHighlights] = useState<HighlightSegment[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isDetecting, setIsDetecting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const refetch = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const data = await highlightService.listHighlights(projectId);
      setHighlights(data.sort((a, b) => a.order - b.order));
    } catch (err) {
      setError(getErrorMessage(err, 'Failed to load highlight segments.'));
    } finally {
      setIsLoading(false);
    }
  }, [projectId]);

  useEffect(() => {
    void refetch();
  }, [refetch]);

  const detect = useCallback(
    async (numShorts?: number) => {
      setIsDetecting(true);
      setError(null);
      try {
        // Fire-and-forget: the backend queues detection via BackgroundTasks
        // and returns 202 immediately, so poll status until it leaves
        // "detecting_highlights" before reading the results back.
        await highlightService.requestHighlightDetection(projectId, numShorts);

        for (let attempt = 0; attempt < DETECT_POLL_MAX_ATTEMPTS; attempt++) {
          await sleep(DETECT_POLL_INTERVAL_MS);
          const statusResponse = await projectService.getProjectStatus(projectId);
          if (statusResponse.status === 'failed') {
            throw new Error(statusResponse.status_message ?? 'Highlight detection failed.');
          }
          if (statusResponse.status !== 'detecting_highlights') break;
        }

        const data = await highlightService.listHighlights(projectId);
        setHighlights(data.sort((a, b) => a.order - b.order));
      } catch (err) {
        setError(getErrorMessage(err, 'Failed to detect highlights.'));
        throw err;
      } finally {
        setIsDetecting(false);
      }
    },
    [projectId]
  );

  const updateHighlight = useCallback(
    async (highlightId: number, payload: UpdateHighlightPayload) => {
      const previous = highlights;
      setHighlights((current) =>
        current.map((h) => (h.id === highlightId ? { ...h, ...payload } : h))
      );
      try {
        const updated = await highlightService.updateHighlight(projectId, highlightId, payload);
        setHighlights((current) => current.map((h) => (h.id === highlightId ? updated : h)));
      } catch (err) {
        setHighlights(previous);
        setError(getErrorMessage(err, 'Failed to update the highlight segment.'));
        throw err;
      }
    },
    [projectId, highlights]
  );

  const removeHighlight = useCallback(
    async (highlightId: number) => {
      const previous = highlights;
      setHighlights((current) => current.filter((h) => h.id !== highlightId));
      try {
        await highlightService.deleteHighlight(projectId, highlightId);
      } catch (err) {
        setHighlights(previous);
        setError(getErrorMessage(err, 'Failed to remove the highlight segment.'));
        throw err;
      }
    },
    [projectId, highlights]
  );

  return { highlights, isLoading, isDetecting, error, refetch, detect, updateHighlight, removeHighlight };
}
