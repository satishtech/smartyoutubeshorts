import { motion } from 'framer-motion';
import { StatusBadge } from '../ui/StatusBadge';
import { ErrorMessage } from '../ui/ErrorMessage';
import { cn } from '../../lib/utils';
import { PIPELINE_STAGES, STAGE_LABELS } from '../../lib/pipelineStages';
import type { ProjectStatus } from '../../types';

const RING_RADIUS = 52;
const RING_CIRCUMFERENCE = 2 * Math.PI * RING_RADIUS;

interface ProgressStatusProps {
  status: ProjectStatus | null;
  statusMessage?: string | null;
  error?: string | null;
  /** Number of highlight segments detected so far, if known. */
  highlightsCount?: number;
  /** How many shorts the user asked for, used alongside highlightsCount. */
  totalRequested?: number;
  /** Whether hard-burned subtitles are enabled for this project. */
  burnSubtitles?: boolean;
  /** Whether B-roll insertion is enabled for this project. */
  useBroll?: boolean;
}

export function ProgressStatus({
  status,
  statusMessage,
  error,
  highlightsCount,
  totalRequested,
  burnSubtitles,
  useBroll,
}: ProgressStatusProps) {
  const currentIndex = status ? PIPELINE_STAGES.indexOf(status) : -1;
  const isFailed = status === 'failed';
  const isCompleted = status === 'completed';

  const percent = isFailed
    ? 0
    : currentIndex < 0
      ? 0
      : Math.round((currentIndex / (PIPELINE_STAGES.length - 1)) * 100);

  const dashOffset = RING_CIRCUMFERENCE * (1 - percent / 100);
  const stageLabel = status ? STAGE_LABELS[status] : 'Waiting';

  return (
    <div className="w-full" data-testid="progress-status">
      <div className="mb-4 flex items-center justify-between">
        <div>
          <p className="text-xs font-semibold uppercase tracking-wider text-pink-400">Processing</p>
          <h3 className="text-sm font-semibold text-gray-600">Pipeline Progress</h3>
        </div>
        {status && <StatusBadge status={status} />}
      </div>

      <ErrorMessage message={error ?? null} />

      {isFailed ? (
        <p className="mt-2 text-sm text-red-400">{statusMessage ?? 'Something went wrong.'}</p>
      ) : (
        <div className="flex flex-col gap-6 sm:flex-row sm:items-center">
          {/* Circular progress ring */}
          <div className="relative mx-auto h-32 w-32 shrink-0 sm:mx-0" aria-hidden="true">
            <svg viewBox="0 0 120 120" className="h-full w-full -rotate-90">
              <defs>
                <linearGradient id="progress-ring-gradient" x1="0%" y1="0%" x2="100%" y2="100%">
                  <stop offset="0%" stopColor="#8b5cf6" />
                  <stop offset="100%" stopColor="#ec4899" />
                </linearGradient>
              </defs>
              <circle cx="60" cy="60" r={RING_RADIUS} strokeWidth="8" className="fill-none stroke-white/10" />
              <motion.circle
                cx="60"
                cy="60"
                r={RING_RADIUS}
                strokeWidth="8"
                strokeLinecap="round"
                className="fill-none"
                stroke={isCompleted ? '#34d399' : 'url(#progress-ring-gradient)'}
                strokeDasharray={RING_CIRCUMFERENCE}
                initial={false}
                animate={{ strokeDashoffset: dashOffset }}
                transition={{ duration: 0.6, ease: 'easeOut' }}
              />
            </svg>
            <div className="absolute inset-0 flex flex-col items-center justify-center">
              <span className="text-2xl font-bold text-gray-800">{percent}%</span>
              <span className="text-[11px] font-medium text-gray-500">{stageLabel}</span>
            </div>
          </div>

          {/* Badge chips */}
          <div className="flex flex-1 flex-wrap items-center gap-2">
            {typeof highlightsCount === 'number' && (
              <span className="inline-flex items-center gap-1.5 rounded-full border border-white/10 bg-white/5 px-3 py-1.5 text-xs font-semibold text-gray-600">
                Highlights: {highlightsCount}
                {typeof totalRequested === 'number' ? `/${totalRequested}` : ''}
              </span>
            )}
            {typeof burnSubtitles === 'boolean' && (
              <TogglePill label="Subtitles" on={burnSubtitles} />
            )}
            {typeof useBroll === 'boolean' && <TogglePill label="B-roll" on={useBroll} />}
          </div>
        </div>
      )}

      {/* Compact stage-by-stage trail. Hidden on md+ where PipelineSidebar
          takes over this role; kept here as the small-viewport fallback. */}
      {!isFailed && (
        <div className="mt-6 flex flex-wrap items-center gap-2 md:hidden">
          {PIPELINE_STAGES.filter((s) => s !== 'completed').map((stage, index) => {
            const isDone = currentIndex > index || status === 'completed';
            const isCurrent = currentIndex === index;
            return (
              <motion.div
                key={stage}
                initial={{ opacity: 0, scale: 0.9 }}
                animate={{ opacity: 1, scale: 1 }}
                className={cn(
                  'flex items-center gap-2 rounded-full px-3 py-1.5 text-xs font-medium transition-colors',
                  isDone
                    ? 'bg-emerald-500/10 text-emerald-400'
                    : isCurrent
                      ? 'bg-gradient-to-r from-violet-500/20 to-pink-500/20 text-pink-300'
                      : 'bg-white/5 text-gray-500'
                )}
              >
                {isCurrent && (
                  <span className="h-2 w-2 animate-pulse rounded-full bg-pink-400" aria-hidden="true" />
                )}
                {STAGE_LABELS[stage]}
              </motion.div>
            );
          })}
        </div>
      )}

      {statusMessage && !isFailed && (
        <p className="mt-3 text-sm text-gray-500">{statusMessage}</p>
      )}
    </div>
  );
}

function TogglePill({ label, on }: { label: string; on: boolean }) {
  return (
    <span
      className={cn(
        'inline-flex items-center gap-2 rounded-full border px-3 py-1.5 text-xs font-semibold',
        on
          ? 'border-emerald-400/30 bg-emerald-500/10 text-emerald-300'
          : 'border-white/10 bg-white/5 text-gray-500'
      )}
    >
      <span className={cn('h-2 w-2 rounded-full', on ? 'bg-emerald-400' : 'bg-gray-500')} />
      {label} {on ? 'ON' : 'OFF'}
    </span>
  );
}
