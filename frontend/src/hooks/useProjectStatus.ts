import { useEffect, useRef, useState } from 'react';
import * as projectService from '../services/projectService';
import { getErrorMessage } from '../services/api';
import type { ProjectStatus } from '../types';

const TERMINAL_STATUSES: ProjectStatus[] = ['completed', 'failed', 'ready_for_review'];
const POLL_INTERVAL_MS = 3000;

interface UseProjectStatusResult {
  status: ProjectStatus | null;
  statusMessage: string | null;
  error: string | null;
  isPolling: boolean;
}

/**
 * Polls GET /api/projects/{id}/status until the pipeline reaches a
 * terminal/reviewable state, then stops.
 */
export function useProjectStatus(
  projectId: number,
  options?: { stopAtReview?: boolean }
): UseProjectStatusResult {
  const [status, setStatus] = useState<ProjectStatus | null>(null);
  const [statusMessage, setStatusMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isPolling, setIsPolling] = useState(true);
  const timeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => {
    let cancelled = false;

    const poll = async () => {
      try {
        const data = await projectService.getProjectStatus(projectId);
        if (cancelled) return;
        setStatus(data.status);
        setStatusMessage(data.status_message);
        setError(null);

        const stopStatuses = options?.stopAtReview
          ? TERMINAL_STATUSES
          : (['completed', 'failed'] as ProjectStatus[]);

        if (stopStatuses.includes(data.status)) {
          setIsPolling(false);
          return;
        }

        timeoutRef.current = setTimeout(() => void poll(), POLL_INTERVAL_MS);
      } catch (err) {
        if (cancelled) return;
        setError(getErrorMessage(err, 'Failed to fetch project status.'));
        setIsPolling(false);
      }
    };

    void poll();

    return () => {
      cancelled = true;
      if (timeoutRef.current) clearTimeout(timeoutRef.current);
    };
  }, [projectId, options?.stopAtReview]);

  return { status, statusMessage, error, isPolling };
}
