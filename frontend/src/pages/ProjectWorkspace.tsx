import { useCallback, useEffect, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { PageWrapper } from '../components/layout/PageWrapper';
import { NavBar } from '../components/layout/NavBar';
import { GlassCard } from '../components/ui/GlassCard';
import { GradientButton } from '../components/ui/GradientButton';
import { ErrorMessage } from '../components/ui/ErrorMessage';
import { Spinner } from '../components/ui/Spinner';
import { TextReveal } from '../components/ui/TextReveal';
import { ProgressStatus } from '../components/ProgressStatus/ProgressStatus';
import { Timeline } from '../components/Timeline/Timeline';
import { useProjectStatus } from '../hooks/useProjectStatus';
import { useHighlights } from '../hooks/useHighlights';
import { useTranscript } from '../hooks/useTranscript';
import { getProject } from '../services/projectService';
import { generateShorts } from '../services/shortService';
import { getErrorMessage } from '../services/api';
import type { Project } from '../types';

const REVIEW_READY_STATUSES = ['ready_for_review', 'generating_shorts', 'completed'];

export default function ProjectWorkspace() {
  const { id } = useParams<{ id: string }>();
  const projectId = Number(id);
  const navigate = useNavigate();

  const [project, setProject] = useState<Project | null>(null);
  const [projectError, setProjectError] = useState<string | null>(null);
  const [isProjectLoading, setIsProjectLoading] = useState(true);
  const [isGenerating, setIsGenerating] = useState(false);
  const [generateError, setGenerateError] = useState<string | null>(null);
  const [showTranscript, setShowTranscript] = useState(false);

  const loadProject = useCallback(async () => {
    if (!Number.isFinite(projectId)) return;
    setIsProjectLoading(true);
    setProjectError(null);
    try {
      const data = await getProject(projectId);
      setProject(data);
    } catch (err) {
      setProjectError(getErrorMessage(err, 'Failed to load this project.'));
    } finally {
      setIsProjectLoading(false);
    }
  }, [projectId]);

  useEffect(() => {
    void loadProject();
  }, [loadProject]);

  const { status, statusMessage, error: statusError } = useProjectStatus(projectId, {
    stopAtReview: true,
  });

  const isReviewReady = status ? REVIEW_READY_STATUSES.includes(status) : false;

  const { transcript, isLoading: isTranscriptLoading, error: transcriptError } = useTranscript(
    projectId,
    isReviewReady
  );

  const {
    highlights,
    isLoading: isHighlightsLoading,
    isDetecting,
    error: highlightsError,
    updateHighlight,
    removeHighlight,
    refetch: refetchHighlights,
    detect: detectHighlights,
  } = useHighlights(projectId);

  useEffect(() => {
    if (isReviewReady) void refetchHighlights();
  }, [isReviewReady, refetchHighlights]);

  const handleGenerate = async () => {
    setIsGenerating(true);
    setGenerateError(null);
    try {
      await generateShorts(projectId);
      navigate(`/projects/${projectId}/results`);
    } catch (err) {
      setGenerateError(getErrorMessage(err, 'Failed to start short generation.'));
    } finally {
      setIsGenerating(false);
    }
  };

  if (!Number.isFinite(projectId)) {
    return (
      <PageWrapper>
        <NavBar />
        <div className="mx-auto max-w-4xl px-6 py-10">
          <ErrorMessage message="Invalid project id." />
        </div>
      </PageWrapper>
    );
  }

  return (
    <PageWrapper>
      <NavBar />
      <div className="mx-auto max-w-4xl px-6 py-10">
        {isProjectLoading ? (
          <Spinner label="Loading project..." />
        ) : projectError ? (
          <ErrorMessage message={projectError} />
        ) : (
          project && <TextReveal as="h1" text={project.title} className="mb-6 text-3xl" />
        )}

        <GlassCard className="mb-6">
          <ProgressStatus
            status={status}
            statusMessage={statusMessage}
            error={statusError}
            highlightsCount={isReviewReady ? highlights.length : undefined}
            totalRequested={project?.num_shorts_requested}
            burnSubtitles={project?.burn_subtitles}
            useBroll={project?.use_broll}
          />
        </GlassCard>

        {isReviewReady && (
          <>
            <GlassCard className="mb-6">
              <div className="mb-3 flex items-center justify-between">
                <h3 className="text-sm font-semibold text-gray-600">Transcript</h3>
                <button
                  type="button"
                  onClick={() => setShowTranscript((v) => !v)}
                  className="text-xs font-medium text-purple-600 hover:underline"
                >
                  {showTranscript ? 'Hide' : 'Show'}
                </button>
              </div>
              {isTranscriptLoading ? (
                <Spinner label="Loading transcript..." />
              ) : transcriptError ? (
                <ErrorMessage message={transcriptError} />
              ) : (
                showTranscript &&
                transcript && (
                  <div className="max-h-64 overflow-y-auto rounded-xl bg-gray-50 p-4 text-sm text-gray-600">
                    {transcript.segments.map((segment, index) => (
                      <p key={index} className="mb-2">
                        <span className="mr-2 font-mono text-xs text-purple-500">
                          {Math.floor(segment.start)}s
                        </span>
                        {segment.text}
                      </p>
                    ))}
                  </div>
                )
              )}
            </GlassCard>

            <GlassCard className="mb-6">
              <h3 className="mb-3 text-sm font-semibold text-gray-600">
                Highlight Timeline ({highlights.length}/{project?.num_shorts_requested ?? '-'})
              </h3>
              <ErrorMessage message={highlightsError} />
              {isHighlightsLoading ? (
                <Spinner label="Loading highlights..." />
              ) : highlights.length === 0 ? (
                <div className="flex flex-col items-start gap-3">
                  <p className="text-sm text-gray-500">No highlight segments detected yet.</p>
                  <GradientButton
                    isLoading={isDetecting}
                    onClick={() => void detectHighlights()}
                  >
                    Detect Highlights
                  </GradientButton>
                </div>
              ) : (
                <Timeline
                  durationSeconds={project?.duration_seconds ?? 0}
                  highlights={highlights}
                  onUpdate={(highlightId, payload) => updateHighlight(highlightId, payload)}
                  onRemove={removeHighlight}
                />
              )}
            </GlassCard>

            <ErrorMessage message={generateError} />
            <GradientButton
              className="w-full"
              isLoading={isGenerating}
              disabled={highlights.length === 0}
              onClick={() => void handleGenerate()}
            >
              Generate Shorts
            </GradientButton>
          </>
        )}
      </div>
    </PageWrapper>
  );
}
