import api, { API_BASE_URL } from './api';
import type { GenerateShortsPayload, Short } from '../types';

export async function generateShorts(
  projectId: number,
  payload?: GenerateShortsPayload
): Promise<Short[]> {
  const { data } = await api.post<Short[]>(`/projects/${projectId}/shorts/generate`, payload ?? {});
  return data;
}

export async function listShorts(projectId: number): Promise<Short[]> {
  const { data } = await api.get<Short[]>(`/projects/${projectId}/shorts`);
  return data;
}

export function getShortStreamUrl(shortId: number): string {
  return `${API_BASE_URL}/shorts/${shortId}/stream`;
}

export function getShortDownloadUrl(shortId: number): string {
  return `${API_BASE_URL}/shorts/${shortId}/download`;
}

export function getProjectDownloadZipUrl(projectId: number): string {
  return `${API_BASE_URL}/projects/${projectId}/download-zip`;
}

/**
 * Download an authenticated binary resource (stream/download/zip endpoints require
 * a Bearer token, so a plain <a href> would 401 — fetch as a blob instead).
 */
export async function downloadAuthenticatedFile(url: string, filename: string): Promise<void> {
  const response = await api.get<Blob>(url, { responseType: 'blob' });
  const blobUrl = window.URL.createObjectURL(response.data);
  const link = document.createElement('a');
  link.href = blobUrl;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  link.remove();
  window.URL.revokeObjectURL(blobUrl);
}
