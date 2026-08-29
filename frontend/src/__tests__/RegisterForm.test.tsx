import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, expect, test, vi, beforeEach } from 'vitest';
import { MemoryRouter } from 'react-router-dom';
import { RegisterForm } from '../components/auth/RegisterForm';
import { AuthProvider } from '../context/AuthContext';
import * as authService from '../services/authService';

vi.mock('../services/authService');

const mockedAuthService = vi.mocked(authService);

function renderRegisterForm() {
  return render(
    <MemoryRouter>
      <AuthProvider>
        <RegisterForm />
      </AuthProvider>
    </MemoryRouter>
  );
}

describe('RegisterForm', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    localStorage.clear();
    mockedAuthService.register.mockResolvedValue({
      id: 1,
      email: 'new@example.com',
      full_name: 'New User',
      created_at: '2026-01-01T00:00:00Z',
    });
    mockedAuthService.login.mockResolvedValue({
      access_token: 'access',
      refresh_token: 'refresh',
      token_type: 'bearer',
    });
    mockedAuthService.fetchCurrentUser.mockResolvedValue({
      id: 1,
      email: 'new@example.com',
      full_name: 'New User',
      created_at: '2026-01-01T00:00:00Z',
    });
  });

  test('renders all registration fields', () => {
    renderRegisterForm();
    expect(screen.getByLabelText(/full name/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/^email$/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/^password$/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/confirm password/i)).toBeInTheDocument();
  });

  test('rejects a short password', async () => {
    const user = userEvent.setup();
    renderRegisterForm();

    await user.type(screen.getByLabelText(/^email$/i), 'new@example.com');
    await user.type(screen.getByLabelText(/^password$/i), 'short');
    await user.type(screen.getByLabelText(/confirm password/i), 'short');
    await user.click(screen.getByRole('button', { name: /create account/i }));

    expect(await screen.findByText(/at least 8 characters/i)).toBeInTheDocument();
    expect(mockedAuthService.register).not.toHaveBeenCalled();
  });

  test('rejects mismatched passwords', async () => {
    const user = userEvent.setup();
    renderRegisterForm();

    await user.type(screen.getByLabelText(/^email$/i), 'new@example.com');
    await user.type(screen.getByLabelText(/^password$/i), 'password123');
    await user.type(screen.getByLabelText(/confirm password/i), 'password456');
    await user.click(screen.getByRole('button', { name: /create account/i }));

    expect(await screen.findByText(/passwords do not match/i)).toBeInTheDocument();
    expect(mockedAuthService.register).not.toHaveBeenCalled();
  });

  test('submits valid registration details', async () => {
    const user = userEvent.setup();
    renderRegisterForm();

    await user.type(screen.getByLabelText(/full name/i), 'New User');
    await user.type(screen.getByLabelText(/^email$/i), 'new@example.com');
    await user.type(screen.getByLabelText(/^password$/i), 'password123');
    await user.type(screen.getByLabelText(/confirm password/i), 'password123');
    await user.click(screen.getByRole('button', { name: /create account/i }));

    await waitFor(() => {
      expect(mockedAuthService.register).toHaveBeenCalledWith({
        email: 'new@example.com',
        password: 'password123',
        full_name: 'New User',
      });
    });
  });
});
