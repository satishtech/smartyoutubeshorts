import { useCallback, useEffect, useState } from 'react';
import * as highlightService from '../services/highlightService';
import { getErrorMessage } from '../services/api';
import type { HighlightSegment, UpdateHighlightPayload } from '../types';

interface UseHighlightsResult {
  highlights: HighlightSegment[];
  isLoading: boolean;
  isDetecting: boolean;
  error: string | null;
  refetch: () => Promise<void>;
  detect: () => Promise<void>;
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

  const detect = useCallback(async () => {
    setIsDetecting(true);
    setError(null);
    try {
      const data = await highlightService.detectHighlights(projectId);
      setHighlights(data.sort((a, b) => a.order - b.order));
    } catch (err) {
      setError(getErrorMessage(err, 'Failed to detect highlights.'));
      throw err;
    } finally {
      setIsDetecting(false);
    }
  }, [projectId]);

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
