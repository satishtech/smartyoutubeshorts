import axios, {
  AxiosError,
  type AxiosRequestConfig,
  type InternalAxiosRequestConfig,
} from 'axios';

const API_BASE_URL = `${import.meta.env.VITE_API_URL ?? 'http://localhost:8000'}/api`;

export const ACCESS_TOKEN_KEY = 'access_token';
export const REFRESH_TOKEN_KEY = 'refresh_token';

const api = axios.create({
  baseURL: API_BASE_URL,
});

interface RetryableConfig extends InternalAxiosRequestConfig {
  _retry?: boolean;
}

api.interceptors.request.use((config) => {
  const token = localStorage.getItem(ACCESS_TOKEN_KEY);
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

let refreshInFlight: Promise<string | null> | null = null;

async function refreshAccessToken(): Promise<string | null> {
  const refreshToken = localStorage.getItem(REFRESH_TOKEN_KEY);
  if (!refreshToken) return null;

  try {
    const { data } = await axios.post<{ access_token: string; refresh_token: string }>(
      `${API_BASE_URL}/auth/refresh`,
      { refresh_token: refreshToken }
    );
    localStorage.setItem(ACCESS_TOKEN_KEY, data.access_token);
    localStorage.setItem(REFRESH_TOKEN_KEY, data.refresh_token);
    return data.access_token;
  } catch {
    localStorage.removeItem(ACCESS_TOKEN_KEY);
    localStorage.removeItem(REFRESH_TOKEN_KEY);
    return null;
  }
}

api.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const originalRequest = error.config as RetryableConfig | undefined;

    if (
      error.response?.status === 401 &&
      originalRequest &&
      !originalRequest._retry &&
      !originalRequest.url?.includes('/auth/refresh')
    ) {
      originalRequest._retry = true;

      if (!refreshInFlight) {
        refreshInFlight = refreshAccessToken().finally(() => {
          refreshInFlight = null;
        });
      }

      const newToken = await refreshInFlight;

      if (newToken) {
        originalRequest.headers.Authorization = `Bearer ${newToken}`;
        return api(originalRequest as AxiosRequestConfig);
      }

      window.dispatchEvent(new CustomEvent('auth:logout'));
    }

    return Promise.reject(error);
  }
);

/**
 * Extract a human-readable message from an Axios/FastAPI error.
 */
export function getErrorMessage(error: unknown, fallback = 'Something went wrong. Please try again.'): string {
  if (axios.isAxiosError(error)) {
    const detail = (error.response?.data as { detail?: unknown } | undefined)?.detail;
    if (typeof detail === 'string') return detail;
    if (Array.isArray(detail) && detail.length > 0) {
      const first = detail[0] as { msg?: string };
      if (first?.msg) return first.msg;
    }
    if (error.message) return error.message;
  }
  if (error instanceof Error) return error.message;
  return fallback;
}

export { API_BASE_URL };
export default api;
