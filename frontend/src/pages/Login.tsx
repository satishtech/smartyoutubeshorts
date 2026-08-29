import { Link } from 'react-router-dom';
import { PageWrapper } from '../components/layout/PageWrapper';
import { MeshBackground } from '../components/layout/MeshBackground';
import { GlassCard } from '../components/ui/GlassCard';
import { TextReveal } from '../components/ui/TextReveal';
import { LoginForm } from '../components/auth/LoginForm';
import { GoogleLoginButton } from '../components/auth/GoogleLoginButton';

export default function Login() {
  return (
    <PageWrapper>
      <MeshBackground />
      <div className="flex min-h-screen items-center justify-center px-4">
        <div className="w-full max-w-md">
          <div className="mb-6 text-center">
            <TextReveal as="h1" text="Welcome back" className="text-3xl" />
            <p className="mt-2 text-sm text-gray-500">Sign in to keep creating shorts.</p>
          </div>
          <GlassCard>
            <LoginForm />
            <div className="my-4 flex items-center gap-3 text-xs text-gray-400">
              <span className="h-px flex-1 bg-gray-200" />
              OR
              <span className="h-px flex-1 bg-gray-200" />
            </div>
            <GoogleLoginButton />
            <p className="mt-6 text-center text-sm text-gray-500">
              Don&apos;t have an account?{' '}
              <Link to="/register" className="font-semibold text-purple-600 hover:underline">
                Create one
              </Link>
            </p>
          </GlassCard>
        </div>
      </div>
    </PageWrapper>
  );
}
