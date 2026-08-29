import { useCallback, useEffect, useState, type ReactNode } from 'react';
import * as authService from '../services/authService';
import { ACCESS_TOKEN_KEY, REFRESH_TOKEN_KEY } from '../services/api';
import { AuthContext, type AuthContextValue } from './authContextInstance';
import type { LoginPayload, RegisterPayload, User } from '../types';

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  const refreshUser = useCallback(async () => {
    const token = localStorage.getItem(ACCESS_TOKEN_KEY);
    if (!token) {
      setUser(null);
      return;
    }
    try {
      const currentUser = await authService.fetchCurrentUser();
      setUser(currentUser);
    } catch {
      setUser(null);
    }
  }, []);

  useEffect(() => {
    const bootstrap = async () => {
      await refreshUser();
      setIsLoading(false);
    };
    void bootstrap();

    const handleForcedLogout = () => setUser(null);
    window.addEventListener('auth:logout', handleForcedLogout);
    return () => window.removeEventListener('auth:logout', handleForcedLogout);
  }, [refreshUser]);

  const login = useCallback(async (payload: LoginPayload) => {
    await authService.login(payload);
    const currentUser = await authService.fetchCurrentUser();
    setUser(currentUser);
  }, []);

  const register = useCallback(async (payload: RegisterPayload) => {
    await authService.register(payload);
    await authService.login({ email: payload.email, password: payload.password });
    const currentUser = await authService.fetchCurrentUser();
    setUser(currentUser);
  }, []);

  const logout = useCallback(async () => {
    await authService.logout();
    setUser(null);
    localStorage.removeItem(REFRESH_TOKEN_KEY);
  }, []);

  const value: AuthContextValue = {
    user,
    isLoading,
    isAuthenticated: user !== null,
    login,
    register,
    logout,
    refreshUser,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}
