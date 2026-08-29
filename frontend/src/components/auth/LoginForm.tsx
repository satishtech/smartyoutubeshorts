import { useState, type FormEvent } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../hooks/useAuth';
import { getErrorMessage } from '../../services/api';
import { AnimatedInput } from '../ui/AnimatedInput';
import { GradientButton } from '../ui/GradientButton';
import { ErrorMessage } from '../ui/ErrorMessage';

interface FormErrors {
  email?: string;
  password?: string;
}

export function LoginForm() {
  const { login } = useAuth();
  const navigate = useNavigate();

  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [fieldErrors, setFieldErrors] = useState<FormErrors>({});
  const [apiError, setApiError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const validate = (): boolean => {
    const errors: FormErrors = {};
    if (!email.trim()) errors.email = 'Email is required';
    if (!password) errors.password = 'Password is required';
    setFieldErrors(errors);
    return Object.keys(errors).length === 0;
  };

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setApiError(null);
    if (!validate()) return;

    setIsSubmitting(true);
    try {
      await login({ email, password });
      navigate('/projects');
    } catch (error) {
      setApiError(getErrorMessage(error, 'Unable to sign in. Check your credentials and try again.'));
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="flex flex-col gap-4" noValidate>
      <ErrorMessage message={apiError} />
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
        autoComplete="current-password"
        value={password}
        onChange={(e) => setPassword(e.target.value)}
        error={fieldErrors.password}
      />
      <GradientButton type="submit" isLoading={isSubmitting} className="mt-2 w-full">
        Sign In
      </GradientButton>
    </form>
  );
}
