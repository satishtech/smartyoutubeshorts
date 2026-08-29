import { motion, type HTMLMotionProps } from 'framer-motion';
import type { ReactNode } from 'react';
import { cn } from '../../lib/utils';

interface GlassCardProps extends HTMLMotionProps<'div'> {
  children: ReactNode;
  className?: string;
}

export function GlassCard({ children, className = '', ...props }: GlassCardProps) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      whileHover={{ scale: 1.02, y: -5 }}
      transition={{ duration: 0.2 }}
      className={cn(
        'rounded-2xl border border-white/10 bg-white/[0.04] p-6 shadow-xl shadow-black/40 backdrop-blur-lg',
        className
      )}
      {...props}
    >
      {children}
    </motion.div>
  );
}
