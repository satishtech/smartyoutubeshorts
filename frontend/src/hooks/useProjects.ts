import { useCallback, useEffect, useState } from 'react';
import * as projectService from '../services/projectService';
import { getErrorMessage } from '../services/api';
import type { Project } from '../types';

interface UseProjectsResult {
  projects: Project[];
  isLoading: boolean;
  error: string | null;
  refetch: () => Promise<void>;
}

export function useProjects(): UseProjectsResult {
  const [projects, setProjects] = useState<Project[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const refetch = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const data = await projectService.listProjects();
      setProjects(data);
    } catch (err) {
      setError(getErrorMessage(err, 'Failed to load your projects.'));
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    void refetch();
  }, [refetch]);

  return { projects, isLoading, error, refetch };
}
