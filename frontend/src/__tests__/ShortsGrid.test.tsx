import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, expect, test, vi, beforeEach } from 'vitest';
import { ShortsGrid } from '../components/ShortsGrid/ShortsGrid';
import * as shortService from '../services/shortService';
import type { Short } from '../types';

vi.mock('../services/shortService', async () => {
  const actual = await vi.importActual<typeof shortService>('../services/shortService');
  return {
    ...actual,
    downloadAuthenticatedFile: vi.fn(),
  };
});

const mockedShortService = vi.mocked(shortService);

function makeShort(overrides: Partial<Short> = {}): Short {
  return {
    id: 1,
    project_id: 1,
    highlight_segment_id: 1,
    file_path: '/storage/1/short-1.mp4',
    thumbnail_path: null,
    duration_seconds: 45,
    has_subtitles: true,
    has_broll: false,
    status: 'ready',
    title: 'Best Moment',
    ...overrides,
  };
}

describe('ShortsGrid', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockedShortService.downloadAuthenticatedFile.mockResolvedValue(undefined);
  });

  test('shows an empty state when there are no shorts', () => {
    render(<ShortsGrid shorts={[]} />);
    expect(screen.getByText(/no shorts have been generated/i)).toBeInTheDocument();
  });

  test('renders a video preview, title, and duration for each ready short', () => {
    render(<ShortsGrid shorts={[makeShort()]} />);
    expect(screen.getByTestId('short-card-1')).toBeInTheDocument();
    expect(screen.getByText('Best Moment')).toBeInTheDocument();
    expect(screen.getByText('0:45')).toBeInTheDocument();
  });

  test('disables the download button while a short is still rendering', () => {
    render(<ShortsGrid shorts={[makeShort({ status: 'rendering' })]} />);
    expect(screen.getByRole('button', { name: /download/i })).toBeDisabled();
  });

  test('triggers an authenticated download when the download button is clicked', async () => {
    const user = userEvent.setup();
    render(<ShortsGrid shorts={[makeShort()]} />);

    await user.click(screen.getByRole('button', { name: /download/i }));

    await waitFor(() => {
      expect(mockedShortService.downloadAuthenticatedFile).toHaveBeenCalledWith(
        shortService.getShortDownloadUrl(1),
        'Best Moment.mp4'
      );
    });
  });

  test('shows an error message if the download fails', async () => {
    mockedShortService.downloadAuthenticatedFile.mockRejectedValueOnce(new Error('network down'));
    const user = userEvent.setup();
    render(<ShortsGrid shorts={[makeShort()]} />);

    await user.click(screen.getByRole('button', { name: /download/i }));

    expect(await screen.findByRole('alert')).toHaveTextContent(/network down/i);
  });
});
