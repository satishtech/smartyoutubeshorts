import { Link, useNavigate } from 'react-router-dom';
import { PageWrapper } from '../components/layout/PageWrapper';
import { NavBar } from '../components/layout/NavBar';
import { GlassCard } from '../components/ui/GlassCard';
import { GradientButton } from '../components/ui/GradientButton';
import { AnimatedList } from '../components/ui/AnimatedList';
import { StatusBadge } from '../components/ui/StatusBadge';
import { ErrorMessage } from '../components/ui/ErrorMessage';
import { Spinner } from '../components/ui/Spinner';
import { TextReveal } from '../components/ui/TextReveal';
import { useProjects } from '../hooks/useProjects';
import { formatDate } from '../lib/utils';

export default function ProjectsDashboard() {
  const { projects, isLoading, error } = useProjects();
  const navigate = useNavigate();

  return (
    <PageWrapper>
      <NavBar />
      <div className="mx-auto max-w-6xl px-6 py-10">
        <div className="mb-8 flex items-center justify-between">
          <div>
            <TextReveal as="h1" text="Your Projects" className="text-3xl" />
            <p className="mt-1 text-sm text-gray-500">
              Pick up where you left off, or start a new one.
            </p>
          </div>
          <GradientButton onClick={() => navigate('/projects/new')}>+ New Project</GradientButton>
        </div>

        <ErrorMessage message={error} />

        {isLoading ? (
          <Spinner label="Loading your projects..." />
        ) : projects.length === 0 ? (
          <GlassCard className="text-center">
            <p className="text-gray-500">You don&apos;t have any projects yet.</p>
            <GradientButton className="mt-4" onClick={() => navigate('/projects/new')}>
              Create your first project
            </GradientButton>
          </GlassCard>
        ) : (
          <AnimatedList className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {projects.map((project) => (
              <Link key={project.id} to={`/projects/${project.id}`} className="block h-full">
                <GlassCard className="flex h-full flex-col gap-3">
                  <div className="flex aspect-video w-full items-center justify-center rounded-xl bg-gradient-to-br from-purple-200 to-pink-200 text-3xl text-white">
                    🎬
                  </div>
                  <div className="flex items-start justify-between gap-2">
                    <h3 className="truncate text-sm font-semibold text-gray-800">{project.title}</h3>
                    <StatusBadge status={project.status} />
                  </div>
                  <p className="mt-auto text-xs text-gray-400">
                    Created {formatDate(project.created_at)}
                  </p>
                </GlassCard>
              </Link>
            ))}
          </AnimatedList>
        )}
      </div>
    </PageWrapper>
  );
}
