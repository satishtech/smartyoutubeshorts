import api from './api';
import type { Transcript } from '../types';

export async function getTranscript(projectId: number): Promise<Transcript> {
  const { data } = await api.get<Transcript>(`/projects/${projectId}/transcript`);
  return data;
}
