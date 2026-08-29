import { PageWrapper } from '../components/layout/PageWrapper';
import { NavBar } from '../components/layout/NavBar';
import { GlassCard } from '../components/ui/GlassCard';
import { TextReveal } from '../components/ui/TextReveal';
import { useAuth } from '../hooks/useAuth';

export default function Profile() {
  const { user } = useAuth();

  return (
    <PageWrapper>
      <NavBar />
      <div className="mx-auto max-w-2xl px-6 py-12">
        <TextReveal as="h1" text="Your Profile" className="mb-6 text-3xl" />
        <GlassCard>
          <dl className="divide-y divide-gray-100">
            <div className="flex justify-between py-3">
              <dt className="text-sm font-medium text-gray-500">Full name</dt>
              <dd className="text-sm text-gray-800">{user?.full_name ?? 'Not set'}</dd>
            </div>
            <div className="flex justify-between py-3">
              <dt className="text-sm font-medium text-gray-500">Email</dt>
              <dd className="text-sm text-gray-800">{user?.email}</dd>
            </div>
            <div className="flex justify-between py-3">
              <dt className="text-sm font-medium text-gray-500">Member since</dt>
              <dd className="text-sm text-gray-800">
                {user?.created_at ? new Date(user.created_at).toLocaleDateString() : '—'}
              </dd>
            </div>
          </dl>
        </GlassCard>
      </div>
    </PageWrapper>
  );
}
