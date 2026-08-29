import { useCallback, useEffect, useState } from 'react';
import * as transcriptService from '../services/transcriptService';
import { getErrorMessage } from '../services/api';
import type { Transcript } from '../types';

interface UseTranscriptResult {
  transcript: Transcript | null;
  isLoading: boolean;
  error: string | null;
  refetch: () => Promise<void>;
}

/**
 * Fetches the transcript once it's available. `enabled` lets the caller
 * defer the request until the pipeline has progressed past transcription.
 */
export function useTranscript(projectId: number, enabled: boolean): UseTranscriptResult {
  const [transcript, setTranscript] = useState<Transcript | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const refetch = useCallback(async () => {
    if (!enabled) return;
    setIsLoading(true);
    setError(null);
    try {
      const data = await transcriptService.getTranscript(projectId);
      setTranscript(data);
    } catch (err) {
      setError(getErrorMessage(err, 'Transcript is not available yet.'));
    } finally {
      setIsLoading(false);
    }
  }, [projectId, enabled]);

  useEffect(() => {
    void refetch();
  }, [refetch]);

  return { transcript, isLoading, error, refetch };
}
