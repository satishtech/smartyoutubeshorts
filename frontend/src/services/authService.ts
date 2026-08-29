import api, { ACCESS_TOKEN_KEY, API_BASE_URL, REFRESH_TOKEN_KEY } from './api';
import type { AuthTokens, LoginPayload, RegisterPayload, User } from '../types';

export async function register(payload: RegisterPayload): Promise<User> {
  const { data } = await api.post<User>('/auth/register', payload);
  return data;
}

export async function login(payload: LoginPayload): Promise<AuthTokens> {
  const { data } = await api.post<AuthTokens>('/auth/login', payload);
  localStorage.setItem(ACCESS_TOKEN_KEY, data.access_token);
  localStorage.setItem(REFRESH_TOKEN_KEY, data.refresh_token);
  return data;
}

export async function fetchCurrentUser(): Promise<User> {
  const { data } = await api.get<User>('/auth/me');
  return data;
}

export async function logout(): Promise<void> {
  const refreshToken = localStorage.getItem(REFRESH_TOKEN_KEY);
  try {
    if (refreshToken) {
      await api.post('/auth/logout', { refresh_token: refreshToken });
    }
  } finally {
    localStorage.removeItem(ACCESS_TOKEN_KEY);
    localStorage.removeItem(REFRESH_TOKEN_KEY);
  }
}

export function storeAuthTokens(tokens: AuthTokens): void {
  localStorage.setItem(ACCESS_TOKEN_KEY, tokens.access_token);
  localStorage.setItem(REFRESH_TOKEN_KEY, tokens.refresh_token);
}

/**
 * URL that kicks off the backend's Google OAuth redirect flow.
 * The backend is responsible for the `state` CSRF check and for
 * redirecting back to the frontend with tokens once complete.
 */
export function getGoogleLoginUrl(): string {
  return `${API_BASE_URL}/auth/google`;
}
