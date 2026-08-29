import { motion } from 'framer-motion';
import { cn } from '../../lib/utils';
import { PIPELINE_STAGES, STAGE_LABELS } from '../../lib/pipelineStages';
import type { ProjectStatus } from '../../types';

interface PipelineSidebarProps {
  status: ProjectStatus | null;
  className?: string;
}

/**
 * Persistent left sidebar for the project workspace/results flow: a vertical
 * list of the pipeline stages with a status indicator per step (completed,
 * current, upcoming). Desktop-only (`md:flex`) — ProgressStatus's compact
 * horizontal trail is the small-viewport fallback for this same information.
 */
export function PipelineSidebar({ status, className = '' }: PipelineSidebarProps) {
  const currentIndex = status ? PIPELINE_STAGES.indexOf(status) : -1;
  const isFailed = status === 'failed';

  return (
    <nav
      aria-label="Pipeline progress"
      data-testid="pipeline-sidebar"
      className={cn(
        'hidden shrink-0 flex-col gap-1 rounded-2xl border border-white/10 bg-white/[0.04] p-4 shadow-xl shadow-black/40 backdrop-blur-lg md:flex md:w-56',
        className
      )}
    >
      <p className="mb-2 px-2 text-xs font-semibold uppercase tracking-wider text-pink-400">
        Pipeline
      </p>

      {PIPELINE_STAGES.map((stage, index) => {
        const isDone = !isFailed && (currentIndex > index || status === 'completed');
        const isCurrent = !isFailed && currentIndex === index;

        return (
          <motion.div
            key={stage}
            data-testid={`pipeline-step-${stage}`}
            initial={{ opacity: 0, x: -8 }}
            animate={{ opacity: 1, x: 0 }}
            className={cn(
              'flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-medium transition-colors',
              isCurrent
                ? 'bg-gradient-to-r from-violet-500/20 to-pink-500/20 text-pink-300'
                : isDone
                  ? 'text-emerald-400'
                  : 'text-gray-500'
            )}
          >
            <span
              aria-hidden="true"
              className={cn(
                'flex h-5 w-5 shrink-0 items-center justify-center rounded-full border text-[10px] font-bold',
                isDone
                  ? 'border-emerald-400/60 bg-emerald-500/20 text-emerald-300'
                  : isCurrent
                    ? 'border-pink-400/60 bg-pink-500/20 text-pink-300'
                    : 'border-white/10 bg-white/5 text-gray-500'
              )}
            >
              {isDone ? '✓' : index + 1}
            </span>
            <span className="truncate">{STAGE_LABELS[stage]}</span>
            {isCurrent && (
              <span
                className="ml-auto h-2 w-2 shrink-0 animate-pulse rounded-full bg-pink-400"
                aria-hidden="true"
              />
            )}
          </motion.div>
        );
      })}

      {isFailed && (
        <p className="mt-2 px-2 text-xs text-red-400">Processing failed.</p>
      )}
    </nav>
  );
}
