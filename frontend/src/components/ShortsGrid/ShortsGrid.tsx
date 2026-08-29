import { useState } from 'react';
import { AnimatedList } from '../ui/AnimatedList';
import { GradientButton } from '../ui/GradientButton';
import { StatusBadge } from '../ui/StatusBadge';
import { ErrorMessage } from '../ui/ErrorMessage';
import { Spinner } from '../ui/Spinner';
import { getErrorMessage } from '../../services/api';
import {
  downloadAuthenticatedFile,
  getShortDownloadUrl,
  getShortStreamUrl,
  getShortThumbnailUrl,
} from '../../services/shortService';
import { useAuthenticatedMediaSrc } from '../../hooks/useAuthenticatedMediaSrc';
import { formatDuration } from '../../lib/utils';
import type { Short } from '../../types';

interface ShortsGridProps {
  shorts: Short[];
}

export function ShortsGrid({ shorts }: ShortsGridProps) {
  if (shorts.length === 0) {
    return <p className="text-sm text-gray-500">No shorts have been generated yet.</p>;
  }

  return (
    <AnimatedList
      className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-3"
      itemClassName="h-full"
    >
      {shorts.map((short) => (
        <ShortCard key={short.id} short={short} />
      ))}
    </AnimatedList>
  );
}

function ShortCard({ short }: { short: Short }) {
  const [downloadingId, setDownloadingId] = useState<number | null>(null);
  const [downloadError, setDownloadError] = useState<string | null>(null);

  const streamUrl = short.status === 'ready' ? getShortStreamUrl(short.id) : null;
  const { src: videoSrc, isLoading: isVideoLoading, error: videoError } =
    useAuthenticatedMediaSrc(streamUrl);

  const thumbnailUrl = short.has_thumbnail ? getShortThumbnailUrl(short.id) : null;
  const { src: posterSrc } = useAuthenticatedMediaSrc(thumbnailUrl);

  const hasTrimmedRange =
    short.highlight_start_time !== null && short.highlight_end_time !== null;

  const handleDownload = async () => {
    setDownloadingId(short.id);
    setDownloadError(null);
    try {
      await downloadAuthenticatedFile(getShortDownloadUrl(short.id), `${short.title ?? `short-${short.id}`}.mp4`);
    } catch (err) {
      setDownloadError(getErrorMessage(err, 'Failed to download this short.'));
    } finally {
      setDownloadingId(null);
    }
  };

  return (
    <div
      data-testid={`short-card-${short.id}`}
      className="flex h-full flex-col overflow-hidden rounded-2xl border border-white/10 bg-white/[0.04] shadow-xl shadow-black/40 backdrop-blur-lg transition-transform hover:-translate-y-1 hover:shadow-2xl"
    >
      <div className="relative aspect-[9/16] w-full bg-black">
        {short.status === 'ready' ? (
          isVideoLoading ? (
            <div className="flex h-full w-full items-center justify-center">
              <Spinner label="Loading preview..." />
            </div>
          ) : videoError || !videoSrc ? (
            <div className="flex h-full w-full items-center justify-center px-4 text-center text-sm text-white/70">
              {videoError ?? 'Preview unavailable.'}
            </div>
          ) : (
            <video
              controls
              preload="metadata"
              className="h-full w-full object-cover"
              src={videoSrc}
              poster={posterSrc ?? undefined}
            >
              Your browser does not support video playback.
            </video>
          )
        ) : (
          <div className="flex h-full w-full items-center justify-center text-sm text-white/70">
            {short.status === 'failed' ? 'Render failed' : 'Rendering...'}
          </div>
        )}
        <span className="absolute left-2 top-2 rounded-full bg-black/60 px-2.5 py-1 text-xs font-semibold text-white backdrop-blur-sm">
          {formatDuration(short.duration_seconds)}
        </span>
        <StatusBadge status={short.status} className="absolute right-2 top-2" />
      </div>
      <div className="flex flex-1 flex-col gap-2 p-4">
        <h4 className="truncate text-sm font-semibold text-gray-800">
          {short.title ?? `Short #${short.id}`}
        </h4>
        {short.highlight_title && (
          <p className="line-clamp-2 text-xs text-gray-500">{short.highlight_title}</p>
        )}
        {hasTrimmedRange && (
          <p className="text-xs font-medium text-gray-400">
            {formatDuration(short.highlight_start_time as number)} –{' '}
            {formatDuration(short.highlight_end_time as number)}
          </p>
        )}
        {(short.has_subtitles || short.has_broll) && (
          <div className="flex flex-wrap gap-1.5">
            {short.has_subtitles && (
              <span className="inline-flex items-center rounded-full border border-white/10 bg-white/5 px-2 py-0.5 text-[10px] font-medium text-gray-500">
                CC
              </span>
            )}
            {short.has_broll && (
              <span className="inline-flex items-center rounded-full border border-white/10 bg-white/5 px-2 py-0.5 text-[10px] font-medium text-gray-500">
                B-roll
              </span>
            )}
          </div>
        )}
        <ErrorMessage message={downloadError} />
        <div className="mt-auto pt-2">
          <GradientButton
            type="button"
            className="w-full text-sm"
            isLoading={downloadingId === short.id}
            disabled={short.status !== 'ready'}
            onClick={() => void handleDownload()}
          >
            Download
          </GradientButton>
        </div>
      </div>
    </div>
  );
}
