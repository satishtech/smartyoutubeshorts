import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, expect, test, vi, beforeEach } from 'vitest';
import { MemoryRouter } from 'react-router-dom';
import { LoginForm } from '../components/auth/LoginForm';
import { AuthProvider } from '../context/AuthContext';
import * as authService from '../services/authService';

vi.mock('../services/authService');

const mockedAuthService = vi.mocked(authService);

function renderLoginForm() {
  return render(
    <MemoryRouter>
      <AuthProvider>
        <LoginForm />
      </AuthProvider>
    </MemoryRouter>
  );
}

describe('LoginForm', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    localStorage.clear();
    mockedAuthService.login.mockResolvedValue({
      access_token: 'access',
      refresh_token: 'refresh',
      token_type: 'bearer',
    });
    mockedAuthService.fetchCurrentUser.mockResolvedValue({
      id: 1,
      email: 'test@example.com',
      full_name: 'Test User',
      created_at: '2026-01-01T00:00:00Z',
    });
  });

  test('renders email and password fields', () => {
    renderLoginForm();
    expect(screen.getByLabelText(/email/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/password/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /sign in/i })).toBeInTheDocument();
  });

  test('shows validation errors when submitted empty', async () => {
    const user = userEvent.setup();
    renderLoginForm();
    await user.click(screen.getByRole('button', { name: /sign in/i }));
    expect(await screen.findByText(/email is required/i)).toBeInTheDocument();
    expect(screen.getByText(/password is required/i)).toBeInTheDocument();
    expect(mockedAuthService.login).not.toHaveBeenCalled();
  });

  test('submits credentials and calls authService.login', async () => {
    const user = userEvent.setup();
    renderLoginForm();

    await user.type(screen.getByLabelText(/email/i), 'test@example.com');
    await user.type(screen.getByLabelText(/password/i), 'password123');
    await user.click(screen.getByRole('button', { name: /sign in/i }));

    await waitFor(() => {
      expect(mockedAuthService.login).toHaveBeenCalledWith({
        email: 'test@example.com',
        password: 'password123',
      });
    });
  });

  test('shows an error message when login fails', async () => {
    mockedAuthService.login.mockRejectedValueOnce({
      isAxiosError: true,
      response: { data: { detail: 'Invalid credentials' } },
    });
    const user = userEvent.setup();
    renderLoginForm();

    await user.type(screen.getByLabelText(/email/i), 'test@example.com');
    await user.type(screen.getByLabelText(/password/i), 'wrongpass');
    await user.click(screen.getByRole('button', { name: /sign in/i }));

    expect(await screen.findByRole('alert')).toBeInTheDocument();
  });
});
