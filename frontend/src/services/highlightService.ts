import api from './api';
import type { HighlightSegment, UpdateHighlightPayload } from '../types';

export async function listHighlights(projectId: number): Promise<HighlightSegment[]> {
  const { data } = await api.get<HighlightSegment[]>(`/projects/${projectId}/highlights`);
  return data;
}

export async function requestHighlightDetection(
  projectId: number,
  numShorts?: number
): Promise<void> {
  // Fire-and-forget: the backend runs detection via BackgroundTasks and
  // returns 202 immediately. The caller must poll project status/highlights
  // to find out when detection actually finishes.
  await api.post(`/projects/${projectId}/highlights/detect`, { num_shorts: numShorts ?? null });
}

export async function updateHighlight(
  projectId: number,
  highlightId: number,
  payload: UpdateHighlightPayload
): Promise<HighlightSegment> {
  const { data } = await api.put<HighlightSegment>(
    `/projects/${projectId}/highlights/${highlightId}`,
    payload
  );
  return data;
}

export async function deleteHighlight(projectId: number, highlightId: number): Promise<void> {
  await api.delete(`/projects/${projectId}/highlights/${highlightId}`);
}
