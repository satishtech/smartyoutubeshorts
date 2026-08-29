import type { ProjectStatus } from '../types';

/**
 * Ordered pipeline stages, shared between ProgressStatus's ring/compact
 * trail and PipelineSidebar's vertical step list so both stay in sync.
 */
export const PIPELINE_STAGES: ProjectStatus[] = [
  'pending',
  'downloading',
  'transcribing',
  'detecting_highlights',
  'ready_for_review',
  'generating_shorts',
  'completed',
];

export const STAGE_LABELS: Record<ProjectStatus, string> = {
  pending: 'Pending',
  downloading: 'Downloading',
  transcribing: 'Transcribing',
  detecting_highlights: 'Analyzing',
  ready_for_review: 'Ready for Review',
  generating_shorts: 'Generating Shorts',
  completed: 'Completed',
  failed: 'Failed',
};
