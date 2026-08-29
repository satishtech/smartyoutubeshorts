import api from './api';
import type { CreateProjectPayload, Project, ProjectListResponse, ProjectStatusResponse } from '../types';

export async function listProjects(): Promise<Project[]> {
  const { data } = await api.get<ProjectListResponse>('/projects');
  return data.items;
}

export async function getProject(projectId: number): Promise<Project> {
  const { data } = await api.get<Project>(`/projects/${projectId}`);
  return data;
}

export async function getProjectStatus(projectId: number): Promise<ProjectStatusResponse> {
  const { data } = await api.get<ProjectStatusResponse>(`/projects/${projectId}/status`);
  return data;
}

export async function deleteProject(projectId: number): Promise<void> {
  await api.delete(`/projects/${projectId}`);
}

export async function createProject(payload: CreateProjectPayload): Promise<Project> {
  if (payload.source_type === 'upload' && payload.file) {
    const form = new FormData();
    form.append('title', payload.title);
    form.append('source_type', payload.source_type);
    form.append('num_shorts_requested', String(payload.num_shorts_requested));
    form.append('burn_subtitles', String(payload.burn_subtitles));
    form.append('use_broll', String(payload.use_broll));
    form.append('file', payload.file);

    const { data } = await api.post<Project>('/projects', form, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return data;
  }

  const { data } = await api.post<Project>('/projects', {
    title: payload.title,
    source_type: payload.source_type,
    source_url: payload.source_url,
    num_shorts_requested: payload.num_shorts_requested,
    burn_subtitles: payload.burn_subtitles,
    use_broll: payload.use_broll,
  });
  return data;
}
