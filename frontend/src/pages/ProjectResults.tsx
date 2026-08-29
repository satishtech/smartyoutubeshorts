import { useCallback, useEffect, useRef, useState } from 'react';
import { useParams } from 'react-router-dom';
import { PageWrapper } from '../components/layout/PageWrapper';
import { NavBar } from '../components/layout/NavBar';
import { PipelineSidebar } from '../components/layout/PipelineSidebar';
import { GlassCard } from '../components/ui/GlassCard';
import { GradientButton } from '../components/ui/GradientButton';
import { ErrorMessage } from '../components/ui/ErrorMessage';
import { Spinner } from '../components/ui/Spinner';
import { TextReveal } from '../components/ui/TextReveal';
import { ShortsGrid } from '../components/ShortsGrid/ShortsGrid';
import { downloadAuthenticatedFile, getProjectDownloadZipUrl, listShorts } from '../services/shortService';
import { getErrorMessage } from '../services/api';
import { useProjectStatus } from '../hooks/useProjectStatus';
import type { Short } from '../types';

const POLL_INTERVAL_MS = 4000;

export default function ProjectResults() {
  const { id } = useParams<{ id: string }>();
  const projectId = Number(id);

  const [shorts, setShorts] = useState<Short[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isDownloadingZip, setIsDownloadingZip] = useState(false);
  const [zipError, setZipError] = useState<string | null>(null);

  const { status } = useProjectStatus(projectId);

  // Mirrors `shorts` so the polling interval always reads the latest
  // value instead of the one captured when the interval was created.
  const shortsRef = useRef<Short[]>(shorts);
  shortsRef.current = shorts;

  const loadShorts = useCallback(async () => {
    if (!Number.isFinite(projectId)) return;
    try {
      const data = await listShorts(projectId);
      setShorts(data);
      setError(null);
    } catch (err) {
      setError(getErrorMessage(err, 'Failed to load shorts for this project.'));
    } finally {
      setIsLoading(false);
    }
  }, [projectId]);

  useEffect(() => {
    void loadShorts();
    const interval = setInterval(() => {
      const stillRendering = shortsRef.current.some(
        (s) => s.status === 'pending' || s.status === 'rendering'
      );
      if (stillRendering) void loadShorts();
    }, POLL_INTERVAL_MS);
    return () => clearInterval(interval);
  }, [loadShorts]);

  const handleDownloadAll = async () => {
    setIsDownloadingZip(true);
    setZipError(null);
    try {
      await downloadAuthenticatedFile(getProjectDownloadZipUrl(projectId), `project-${projectId}-shorts.zip`);
    } catch (err) {
      setZipError(getErrorMessage(err, 'Failed to download the ZIP archive.'));
    } finally {
      setIsDownloadingZip(false);
    }
  };

  return (
    <PageWrapper>
      <NavBar />
      <div className="mx-auto max-w-6xl px-6 py-10">
        <div className="flex flex-col gap-6 md:flex-row md:items-start">
          <PipelineSidebar status={status} className="md:sticky md:top-24" />

          <div className="min-w-0 flex-1">
            <TextReveal as="h1" text="Your Shorts" className="mb-6 text-3xl" />

            <GlassCard>
              <div className="mb-6 flex flex-wrap items-center justify-between gap-4">
                <p className="text-xs font-semibold uppercase tracking-wider text-gray-500">Clips Output</p>
                <GradientButton
                  isLoading={isDownloadingZip}
                  disabled={shorts.every((s) => s.status !== 'ready')}
                  onClick={() => void handleDownloadAll()}
                >
                  Download All (.zip)
                </GradientButton>
              </div>

              <ErrorMessage message={zipError} />
              <ErrorMessage message={error} />

              {isLoading ? <Spinner label="Loading your shorts..." /> : <ShortsGrid shorts={shorts} />}
            </GlassCard>
          </div>
        </div>
      </div>
    </PageWrapper>
  );
}
