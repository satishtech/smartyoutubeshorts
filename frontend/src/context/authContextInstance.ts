import { createContext } from 'react';
import type { LoginPayload, RegisterPayload, User } from '../types';

export interface AuthContextValue {
  user: User | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  login: (payload: LoginPayload) => Promise<void>;
  register: (payload: RegisterPayload) => Promise<void>;
  logout: () => Promise<void>;
  refreshUser: () => Promise<void>;
}

// Kept in its own module (rather than alongside the AuthProvider component)
// so context/AuthContext.tsx only exports a component, per the
// react-refresh/only-export-components rule.
export const AuthContext = createContext<AuthContextValue | undefined>(undefined);
