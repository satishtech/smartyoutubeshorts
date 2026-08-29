// ---------------------------------------------------------------------------
// Domain types mirroring the backend models (see INITIAL.md).
// No `any` anywhere per CLAUDE.md.
// ---------------------------------------------------------------------------

export interface User {
  id: number;
  email: string;
  full_name: string | null;
  created_at: string;
}

export interface AuthTokens {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

export interface RegisterPayload {
  email: string;
  password: string;
  full_name?: string;
}

export interface LoginPayload {
  email: string;
  password: string;
}

// ---------------------------------------------------------------------------
// Projects
// ---------------------------------------------------------------------------

export type ProjectSourceType = 'upload' | 'youtube_url';

export type ProjectStatus =
  | 'pending'
  | 'downloading'
  | 'transcribing'
  | 'detecting_highlights'
  | 'ready_for_review'
  | 'generating_shorts'
  | 'completed'
  | 'failed';

export interface Project {
  id: number;
  user_id: number;
  title: string;
  source_type: ProjectSourceType;
  source_url: string | null;
  source_video_path: string | null;
  duration_seconds: number | null;
  status: ProjectStatus;
  status_message: string | null;
  num_shorts_requested: number;
  burn_subtitles: boolean;
  use_broll: boolean;
  created_at: string;
  updated_at: string;
}

export interface CreateProjectPayload {
  title: string;
  source_type: ProjectSourceType;
  source_url?: string;
  num_shorts_requested: number;
  burn_subtitles: boolean;
  use_broll: boolean;
  file?: File;
}

export interface ProjectStatusResponse {
  id: number;
  status: ProjectStatus;
  status_message: string | null;
}

export interface ProjectListResponse {
  items: Project[];
  total: number;
}

// ---------------------------------------------------------------------------
// Transcripts
// ---------------------------------------------------------------------------

export interface TranscriptSegment {
  start: number;
  end: number;
  text: string;
}

export interface Transcript {
  id: number;
  project_id: number;
  full_text: string;
  segments: TranscriptSegment[];
  language: string;
}

// ---------------------------------------------------------------------------
// Highlight segments
// ---------------------------------------------------------------------------

export interface HighlightSegment {
  id: number;
  project_id: number;
  order: number;
  start_time: number;
  end_time: number;
  title: string;
  reason: string;
  score: number;
  created_at: string;
  updated_at: string;
}

export interface UpdateHighlightPayload {
  start_time?: number;
  end_time?: number;
  title?: string;
}

// ---------------------------------------------------------------------------
// Shorts
// ---------------------------------------------------------------------------

export type ShortStatus = 'pending' | 'rendering' | 'ready' | 'failed';

export interface Short {
  id: number;
  project_id: number;
  highlight_segment_id: number;
  file_path: string;
  thumbnail_path: string | null;
  duration_seconds: number;
  has_subtitles: boolean;
  has_broll: boolean;
  status: ShortStatus;
  title?: string;
}

export interface GenerateShortsPayload {
  highlight_segment_ids?: number[];
}

// ---------------------------------------------------------------------------
// Generic API error shape
// ---------------------------------------------------------------------------

export interface ApiErrorDetail {
  detail?: string | { msg: string; loc?: (string | number)[] }[];
}
