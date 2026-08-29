import { motion } from 'framer-motion';
import { cn } from '../../lib/utils';

interface TextRevealProps {
  text: string;
  as?: 'h1' | 'h2' | 'h3';
  className?: string;
}

export function TextReveal({ text, as = 'h1', className = '' }: TextRevealProps) {
  // Cast to a single concrete variant: motion.h1/h2/h3 differ only in the
  // underlying HTML element type, which is irrelevant to the props used here,
  // and indexing with a union `as` otherwise produces an unwieldy union type.
  const Component = motion[as] as typeof motion.h1;
  return (
    <Component
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5, ease: 'easeOut' }}
      className={cn(
        'bg-gradient-to-r from-purple-600 to-pink-500 bg-clip-text font-bold text-transparent',
        className
      )}
    >
      {text}
    </Component>
  );
}
