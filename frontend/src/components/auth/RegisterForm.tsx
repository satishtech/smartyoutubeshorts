import { useState, type FormEvent } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../hooks/useAuth';
import { getErrorMessage } from '../../services/api';
import { AnimatedInput } from '../ui/AnimatedInput';
import { GradientButton } from '../ui/GradientButton';
import { ErrorMessage } from '../ui/ErrorMessage';

interface FormErrors {
  fullName?: string;
  email?: string;
  password?: string;
  confirmPassword?: string;
}

export function RegisterForm() {
  const { register } = useAuth();
  const navigate = useNavigate();

  const [fullName, setFullName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [fieldErrors, setFieldErrors] = useState<FormErrors>({});
  const [apiError, setApiError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const validate = (): boolean => {
    const errors: FormErrors = {};
    if (!email.trim()) errors.email = 'Email is required';
    if (!password) errors.password = 'Password is required';
    else if (password.length < 8) errors.password = 'Password must be at least 8 characters';
    if (confirmPassword !== password) errors.confirmPassword = 'Passwords do not match';
    setFieldErrors(errors);
    return Object.keys(errors).length === 0;
  };

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setApiError(null);
    if (!validate()) return;

    setIsSubmitting(true);
    try {
      await register({ email, password, full_name: fullName || undefined });
      navigate('/projects');
    } catch (error) {
      setApiError(getErrorMessage(error, 'Unable to create your account. Please try again.'));
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="flex flex-col gap-4" noValidate>
      <ErrorMessage message={apiError} />
      <AnimatedInput
        label="Full name"
        name="fullName"
        type="text"
        autoComplete="name"
        value={fullName}
        onChange={(e) => setFullName(e.target.value)}
        error={fieldErrors.fullName}
      />
      <AnimatedInput
        label="Email"
        name="email"
        type="email"
        autoComplete="email"
        value={email}
        onChange={(e) => setEmail(e.target.value)}
        error={fieldErrors.email}
      />
      <AnimatedInput
        label="Password"
        name="password"
        type="password"
        autoComplete="new-password"
        value={password}
        onChange={(e) => setPassword(e.target.value)}
        error={fieldErrors.password}
      />
      <AnimatedInput
        label="Confirm password"
        name="confirmPassword"
        type="password"
        autoComplete="new-password"
        value={confirmPassword}
        onChange={(e) => setConfirmPassword(e.target.value)}
        error={fieldErrors.confirmPassword}
      />
      <GradientButton type="submit" isLoading={isSubmitting} className="mt-2 w-full">
        Create Account
      </GradientButton>
    </form>
  );
}
