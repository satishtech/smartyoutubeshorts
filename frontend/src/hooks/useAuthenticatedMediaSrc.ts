import { useEffect, useState } from 'react';
import api from '../services/api';

/**
 * Fetches an authenticated media URL (stream/download endpoints require a
 * Bearer token, which a plain <video src> can't send) as a blob and exposes
 * it as an object URL. Short clips are small enough that loading the whole
 * blob up front is simpler and safer than a query-param token.
 */
export function useAuthenticatedMediaSrc(url: string | null): {
  src: string | null;
  isLoading: boolean;
  error: string | null;
} {
  const [src, setSrc] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(Boolean(url));
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!url) {
      setSrc(null);
      setIsLoading(false);
      return;
    }

    let cancelled = false;
    let objectUrl: string | null = null;
    setIsLoading(true);
    setError(null);

    void (async () => {
      try {
        const response = await api.get<Blob>(url, { responseType: 'blob' });
        if (cancelled) return;
        objectUrl = window.URL.createObjectURL(response.data);
        setSrc(objectUrl);
      } catch {
        if (!cancelled) setError('Failed to load video preview.');
      } finally {
        if (!cancelled) setIsLoading(false);
      }
    })();

    return () => {
      cancelled = true;
      if (objectUrl) window.URL.revokeObjectURL(objectUrl);
    };
  }, [url]);

  return { src, isLoading, error };
}
