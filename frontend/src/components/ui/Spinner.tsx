import { cn } from '../../lib/utils';

interface SpinnerProps {
  className?: string;
  label?: string;
}

export function Spinner({ className = '', label = 'Loading...' }: SpinnerProps) {
  return (
    <div className="flex items-center justify-center gap-3 py-8" role="status" aria-live="polite">
      <span
        className={cn(
          'h-8 w-8 animate-spin rounded-full border-4 border-white/10 border-t-pink-500',
          className
        )}
      />
      <span className="text-sm text-gray-500">{label}</span>
    </div>
  );
}
