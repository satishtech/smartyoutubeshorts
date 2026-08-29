import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, expect, test, vi, beforeEach } from 'vitest';
import { ShortsGrid } from '../components/ShortsGrid/ShortsGrid';
import * as shortService from '../services/shortService';
import api from '../services/api';
import type { Short } from '../types';

vi.mock('../services/shortService', async () => {
  const actual = await vi.importActual<typeof shortService>('../services/shortService');
  return {
    ...actual,
    downloadAuthenticatedFile: vi.fn(),
  };
});

vi.mock('../services/api', async () => {
  const actual = await vi.importActual<typeof import('../services/api')>('../services/api');
  return {
    ...actual,
    default: { ...actual.default, get: vi.fn() },
  };
});

const mockedShortService = vi.mocked(shortService);
const mockedApiGet = vi.mocked(api.get);

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
    has_thumbnail: false,
    highlight_title: null,
    highlight_start_time: null,
    highlight_end_time: null,
    status: 'ready',
    title: 'Best Moment',
    ...overrides,
  };
}

describe('ShortsGrid', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockedShortService.downloadAuthenticatedFile.mockResolvedValue(undefined);
    mockedApiGet.mockResolvedValue({ data: new Blob(['fake-video']) });
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

  test('renders the linked highlight excerpt and trimmed duration range', () => {
    render(
      <ShortsGrid
        shorts={[
          makeShort({
            highlight_title: 'The moment everything clicked',
            highlight_start_time: 78,
            highlight_end_time: 138,
          }),
        ]}
      />
    );
    expect(screen.getByText('The moment everything clicked')).toBeInTheDocument();
    expect(screen.getByText('1:18 – 2:18')).toBeInTheDocument();
  });

  test('fetches an authenticated poster image when the short has a thumbnail', async () => {
    render(<ShortsGrid shorts={[makeShort({ has_thumbnail: true })]} />);

    await waitFor(() => {
      expect(mockedApiGet).toHaveBeenCalledWith(
        shortService.getShortThumbnailUrl(1),
        expect.objectContaining({ responseType: 'blob' })
      );
    });
  });
});
