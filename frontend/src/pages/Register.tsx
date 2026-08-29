import { Link } from 'react-router-dom';
import { PageWrapper } from '../components/layout/PageWrapper';
import { MeshBackground } from '../components/layout/MeshBackground';
import { GlassCard } from '../components/ui/GlassCard';
import { TextReveal } from '../components/ui/TextReveal';
import { RegisterForm } from '../components/auth/RegisterForm';
import { GoogleLoginButton } from '../components/auth/GoogleLoginButton';

export default function Register() {
  return (
    <PageWrapper>
      <MeshBackground />
      <div className="flex min-h-screen items-center justify-center px-4">
        <div className="w-full max-w-md">
          <div className="mb-6 text-center">
            <TextReveal as="h1" text="Create your account" className="text-3xl" />
            <p className="mt-2 text-sm text-gray-500">
              Turn long videos into scroll-stopping shorts.
            </p>
          </div>
          <GlassCard>
            <RegisterForm />
            <div className="my-4 flex items-center gap-3 text-xs text-gray-400">
              <span className="h-px flex-1 bg-gray-200" />
              OR
              <span className="h-px flex-1 bg-gray-200" />
            </div>
            <GoogleLoginButton />
            <p className="mt-6 text-center text-sm text-gray-500">
              Already have an account?{' '}
              <Link to="/login" className="font-semibold text-purple-600 hover:underline">
                Sign in
              </Link>
            </p>
          </GlassCard>
        </div>
      </div>
    </PageWrapper>
  );
}
