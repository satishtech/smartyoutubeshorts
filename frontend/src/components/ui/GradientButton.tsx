import { motion, type HTMLMotionProps } from 'framer-motion';
import type { ReactNode } from 'react';
import { cn } from '../../lib/utils';

interface GradientButtonProps extends HTMLMotionProps<'button'> {
  children: ReactNode;
  isLoading?: boolean;
  variant?: 'primary' | 'danger' | 'ghost';
}

export function GradientButton({
  children,
  className = '',
  isLoading = false,
  variant = 'primary',
  disabled,
  ...props
}: GradientButtonProps) {
  const variantClasses: Record<NonNullable<GradientButtonProps['variant']>, string> = {
    primary: 'bg-gradient-to-r from-violet-500 to-pink-500 text-white shadow-lg shadow-pink-500/20',
    danger: 'bg-gradient-to-r from-red-500 to-rose-500 text-white shadow-lg shadow-red-500/20',
    ghost: 'bg-white/5 text-gray-700 border border-white/10 hover:bg-white/10',
  };

  return (
    <motion.button
      whileHover={disabled || isLoading ? undefined : { scale: 1.02, y: -2 }}
      whileTap={disabled || isLoading ? undefined : { scale: 0.98 }}
      disabled={disabled || isLoading}
      className={cn(
        'inline-flex items-center justify-center gap-2 rounded-full px-6 py-3 font-semibold shadow-md transition-shadow hover:shadow-lg disabled:cursor-not-allowed disabled:opacity-60',
        variantClasses[variant],
        className
      )}
      {...props}
    >
      {isLoading && (
        <span
          className="h-4 w-4 animate-spin rounded-full border-2 border-white/60 border-t-white"
          aria-hidden="true"
        />
      )}
      {children}
    </motion.button>
  );
}
