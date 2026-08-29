import { useState, type ChangeEvent, type FormEvent } from 'react';
import { motion } from 'framer-motion';
import { AnimatedInput } from '../ui/AnimatedInput';
import { GradientButton } from '../ui/GradientButton';
import { ErrorMessage } from '../ui/ErrorMessage';
import { cn } from '../../lib/utils';
import type { CreateProjectPayload, OutputLayout, ProjectSourceType } from '../../types';

const MAX_UPLOAD_BYTES = 2 * 1024 * 1024 * 1024; // 2GB
const ACCEPTED_VIDEO_TYPES = ['video/mp4', 'video/quicktime', 'video/x-matroska', 'video/webm'];
const YOUTUBE_URL_PATTERN = /^(https?:\/\/)?(www\.)?(youtube\.com\/watch\?v=|youtu\.be\/)[\w-]+/i;

const OUTPUT_LAYOUT_OPTIONS: { value: OutputLayout; label: string }[] = [
  { value: 'vertical_9_16', label: '9:16 Vertical (Shorts/Reels/TikTok)' },
  { value: 'square_1_1', label: '1:1 Square (Instagram/Facebook feed)' },
  { value: 'portrait_4_5', label: '4:5 Portrait (Instagram feed)' },
  { value: 'landscape_16_9', label: '16:9 Landscape (YouTube/Twitter)' },
  { value: 'classic_4_3', label: '4:3 Classic' },
];

interface UploadFormProps {
  onSubmit: (payload: CreateProjectPayload) => Promise<void>;
  isSubmitting: boolean;
}

export function UploadForm({ onSubmit, isSubmitting }: UploadFormProps) {
  const [sourceType, setSourceType] = useState<ProjectSourceType>('upload');
  const [title, setTitle] = useState('');
  const [file, setFile] = useState<File | null>(null);
  const [sourceUrl, setSourceUrl] = useState('');
  const [numShorts, setNumShorts] = useState(3);
  const [burnSubtitles, setBurnSubtitles] = useState(true);
  const [useBroll, setUseBroll] = useState(false);
  const [outputLayout, setOutputLayout] = useState<OutputLayout>('vertical_9_16');
  const [error, setError] = useState<string | null>(null);

  const handleFileChange = (event: ChangeEvent<HTMLInputElement>) => {
    const selected = event.target.files?.[0] ?? null;
    if (selected && !ACCEPTED_VIDEO_TYPES.includes(selected.type)) {
      setError('Please choose an MP4, MOV, MKV, or WebM video file.');
      setFile(null);
      return;
    }
    if (selected && selected.size > MAX_UPLOAD_BYTES) {
      setError('File is too large. Maximum upload size is 2GB.');
      setFile(null);
      return;
    }
    setError(null);
    setFile(selected);
  };

  const validate = (): boolean => {
    if (!title.trim()) {
      setError('Please give your project a title.');
      return false;
    }
    if (sourceType === 'upload' && !file) {
      setError('Please choose a video file to upload.');
      return false;
    }
    if (sourceType === 'youtube_url' && !YOUTUBE_URL_PATTERN.test(sourceUrl.trim())) {
      setError('Please enter a valid YouTube URL.');
      return false;
    }
    setError(null);
    return true;
  };

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!validate()) return;

    const payload: CreateProjectPayload = {
      title: title.trim(),
      source_type: sourceType,
      num_shorts_requested: numShorts,
      burn_subtitles: burnSubtitles,
      use_broll: useBroll,
      output_layout: outputLayout,
      ...(sourceType === 'upload' ? { file: file ?? undefined } : { source_url: sourceUrl.trim() }),
    };

    try {
      await onSubmit(payload);
    } catch {
      // Parent surfaces the request error; keep the form interactive.
    }
  };

  return (
    <form onSubmit={handleSubmit} className="flex flex-col gap-6" noValidate>
      <ErrorMessage message={error} />

      <AnimatedInput
        label="Project title"
        name="title"
        placeholder="My awesome podcast episode"
        value={title}
        onChange={(e) => setTitle(e.target.value)}
      />

      <div>
        <p className="mb-2 text-sm font-medium text-gray-700">Video source</p>
        <div className="flex gap-2">
          {(['upload', 'youtube_url'] as ProjectSourceType[]).map((type) => (
            <motion.button
              key={type}
              type="button"
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
              onClick={() => setSourceType(type)}
              className={cn(
                'flex-1 rounded-xl border-2 px-4 py-3 text-sm font-medium transition-colors',
                sourceType === type
                  ? 'border-pink-400/60 bg-pink-500/10 text-pink-300'
                  : 'border-gray-200 text-gray-500 hover:border-gray-300'
              )}
            >
              {type === 'upload' ? 'Upload a file' : 'Paste a YouTube URL'}
            </motion.button>
          ))}
        </div>
      </div>

      {sourceType === 'upload' ? (
        <div>
          <label htmlFor="video-file" className="mb-1 block text-sm font-medium text-gray-700">
            Video file
          </label>
          <input
            id="video-file"
            name="file"
            type="file"
            accept={ACCEPTED_VIDEO_TYPES.join(',')}
            onChange={handleFileChange}
            className="block w-full rounded-xl border-2 border-dashed border-gray-200 px-4 py-6 text-sm text-gray-500 file:mr-4 file:rounded-full file:border-0 file:bg-pink-500/10 file:px-4 file:py-2 file:text-sm file:font-semibold file:text-pink-300 hover:border-purple-300"
          />
          {file && <p className="mt-2 text-xs text-gray-500">Selected: {file.name}</p>}
        </div>
      ) : (
        <AnimatedInput
          label="YouTube URL"
          name="sourceUrl"
          placeholder="https://www.youtube.com/watch?v=..."
          value={sourceUrl}
          onChange={(e) => setSourceUrl(e.target.value)}
        />
      )}

      <div>
        <label htmlFor="num-shorts" className="mb-1 block text-sm font-medium text-gray-700">
          Number of shorts: <span className="font-semibold text-purple-600">{numShorts}</span>
        </label>
        <input
          id="num-shorts"
          type="range"
          min={1}
          max={10}
          step={1}
          value={numShorts}
          onChange={(e) => setNumShorts(Number(e.target.value))}
          className="w-full accent-purple-500"
        />
        <div className="mt-1 flex justify-between text-xs text-gray-400">
          <span>1</span>
          <span>10</span>
        </div>
      </div>

      <div>
        <label htmlFor="output-layout" className="mb-1 block text-sm font-medium text-gray-700">
          Output layout
        </label>
        <select
          id="output-layout"
          name="outputLayout"
          value={outputLayout}
          onChange={(e) => setOutputLayout(e.target.value as OutputLayout)}
          className="w-full rounded-xl border-2 border-gray-200 bg-white/5 px-4 py-3 text-gray-800 outline-none transition-colors focus:border-purple-500"
        >
          {OUTPUT_LAYOUT_OPTIONS.map((option) => (
            <option key={option.value} value={option.value}>
              {option.label}
            </option>
          ))}
        </select>
      </div>

      <div className="flex flex-col gap-3">
        <ToggleRow
          label="Burn subtitles into the video"
          description="Hard-burned captions on every short (recommended)"
          checked={burnSubtitles}
          onChange={setBurnSubtitles}
        />
        <ToggleRow
          label="Use B-roll footage"
          description="Adds relevant stock footage where available"
          checked={useBroll}
          onChange={setUseBroll}
        />
      </div>

      <GradientButton type="submit" isLoading={isSubmitting} className="w-full">
        Create Project
      </GradientButton>
    </form>
  );
}

interface ToggleRowProps {
  label: string;
  description: string;
  checked: boolean;
  onChange: (value: boolean) => void;
}

function ToggleRow({ label, description, checked, onChange }: ToggleRowProps) {
  return (
    <div className="flex items-center justify-between rounded-xl border border-gray-200 px-4 py-3">
      <div>
        <p className="text-sm font-medium text-gray-700">{label}</p>
        <p className="text-xs text-gray-400">{description}</p>
      </div>
      <motion.button
        type="button"
        role="switch"
        aria-checked={checked}
        aria-label={label}
        whileTap={{ scale: 0.95 }}
        onClick={() => onChange(!checked)}
        className={cn(
          'relative h-6 w-11 shrink-0 rounded-full transition-colors',
          checked ? 'bg-purple-500' : 'bg-gray-200'
        )}
      >
        <motion.span
          layout
          className="absolute top-0.5 h-5 w-5 rounded-full bg-white shadow"
          style={{ left: checked ? '1.375rem' : '0.125rem' }}
        />
      </motion.button>
    </div>
  );
}
