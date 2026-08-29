import { motion } from 'framer-motion';
import { forwardRef, type InputHTMLAttributes } from 'react';
import { cn } from '../../lib/utils';

interface AnimatedInputProps
  extends Omit<
    InputHTMLAttributes<HTMLInputElement>,
    'onAnimationStart' | 'onAnimationEnd' | 'onAnimationIteration' | 'onDrag' | 'onDragStart' | 'onDragEnd'
  > {
  label?: string;
  error?: string;
}

export const AnimatedInput = forwardRef<HTMLInputElement, AnimatedInputProps>(
  ({ label, error, className = '', id, ...props }, ref) => {
    const inputId = id ?? props.name;
    return (
      <div className="w-full">
        {label && (
          <label htmlFor={inputId} className="mb-1 block text-sm font-medium text-gray-700">
            {label}
          </label>
        )}
        <motion.input
          ref={ref}
          id={inputId}
          whileFocus={{ scale: 1.01 }}
          className={cn(
            'w-full rounded-xl border-2 bg-white/5 px-4 py-3 text-gray-800 outline-none transition-colors placeholder:text-gray-500',
            error ? 'border-red-500' : 'border-gray-200 focus:border-purple-500',
            className
          )}
          aria-invalid={Boolean(error)}
          {...props}
        />
        {error && <p className="mt-1 text-sm text-red-500">{error}</p>}
      </div>
    );
  }
);

AnimatedInput.displayName = 'AnimatedInput';
