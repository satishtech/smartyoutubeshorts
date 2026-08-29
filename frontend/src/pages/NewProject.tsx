import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { PageWrapper } from '../components/layout/PageWrapper';
import { NavBar } from '../components/layout/NavBar';
import { GlassCard } from '../components/ui/GlassCard';
import { TextReveal } from '../components/ui/TextReveal';
import { ErrorMessage } from '../components/ui/ErrorMessage';
import { UploadForm } from '../components/UploadForm/UploadForm';
import { createProject } from '../services/projectService';
import { getErrorMessage } from '../services/api';
import type { CreateProjectPayload } from '../types';

export default function NewProject() {
  const navigate = useNavigate();
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (payload: CreateProjectPayload) => {
    setIsSubmitting(true);
    setError(null);
    try {
      const project = await createProject(payload);
      navigate(`/projects/${project.id}`);
    } catch (err) {
      setError(getErrorMessage(err, 'Failed to create your project. Please try again.'));
      throw err;
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <PageWrapper>
      <NavBar />
      <div className="mx-auto max-w-2xl px-6 py-10">
        <TextReveal as="h1" text="Start a New Project" className="mb-2 text-3xl" />
        <p className="mb-6 text-sm text-gray-500">
          Upload a video or paste a YouTube URL and we&apos;ll turn it into shorts.
        </p>
        <ErrorMessage message={error} />
        <GlassCard className="mt-4">
          <UploadForm onSubmit={handleSubmit} isSubmitting={isSubmitting} />
        </GlassCard>
      </div>
    </PageWrapper>
  );
}
