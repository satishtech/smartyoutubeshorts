import { cn } from '../../lib/utils';
import type { ProjectStatus, ShortStatus } from '../../types';

const STATUS_STYLES: Record<string, string> = {
  pending: 'border border-white/10 bg-white/5 text-gray-500',
  downloading: 'border border-blue-500/30 bg-blue-500/10 text-blue-300',
  transcribing: 'border border-indigo-500/30 bg-indigo-500/10 text-indigo-300',
  detecting_highlights: 'border border-purple-500/30 bg-purple-500/10 text-purple-300',
  ready_for_review: 'border border-amber-500/30 bg-amber-500/10 text-amber-300',
  generating_shorts: 'border border-pink-500/30 bg-pink-500/10 text-pink-300',
  rendering: 'border border-pink-500/30 bg-pink-500/10 text-pink-300',
  ready: 'border border-emerald-500/30 bg-emerald-500/10 text-emerald-300',
  completed: 'border border-emerald-500/30 bg-emerald-500/10 text-emerald-300',
  failed: 'border border-red-500/30 bg-red-500/10 text-red-300',
};

const STATUS_LABELS: Record<string, string> = {
  pending: 'Pending',
  downloading: 'Downloading',
  transcribing: 'Transcribing',
  detecting_highlights: 'Detecting Highlights',
  ready_for_review: 'Ready for Review',
  generating_shorts: 'Generating Shorts',
  rendering: 'Rendering',
  ready: 'Ready',
  completed: 'Completed',
  failed: 'Failed',
};

interface StatusBadgeProps {
  status: ProjectStatus | ShortStatus;
  className?: string;
}

export function StatusBadge({ status, className = '' }: StatusBadgeProps) {
  return (
    <span
      className={cn(
        'inline-flex items-center rounded-full px-3 py-1 text-xs font-semibold',
        STATUS_STYLES[status] ?? 'bg-gray-100 text-gray-600',
        className
      )}
    >
      {STATUS_LABELS[status] ?? status}
    </span>
  );
}
