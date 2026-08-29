import api from './api';
import type { HighlightSegment, UpdateHighlightPayload } from '../types';

export async function listHighlights(projectId: number): Promise<HighlightSegment[]> {
  const { data } = await api.get<HighlightSegment[]>(`/projects/${projectId}/highlights`);
  return data;
}

export async function detectHighlights(projectId: number): Promise<HighlightSegment[]> {
  const { data } = await api.post<HighlightSegment[]>(`/projects/${projectId}/highlights/detect`);
  return data;
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
