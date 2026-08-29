/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        brand: {
          purple: '#8b5cf6',
          pink: '#ec4899',
        },
        // Dark-mode surface tokens used by the app shell (page bg vs. card bg).
        base: {
          DEFAULT: '#0a0a0f',
          raised: '#0d0d14',
        },
        // The default Tailwind `gray` scale is remapped (not extended) for a
        // dark-first UI: the app's existing components already use gray-* for
        // text/border/bg (e.g. `text-gray-700`, `bg-gray-100`, `border-gray-200`).
        // Re-pointing those shades to a near-black-to-white scale lets every
        // existing component render correctly on the new dark background
        // without touching each file's classNames individually. Relative
        // weight is preserved: gray-900 stays the strongest/brightest text,
        // gray-400 stays the most de-emphasized.
        gray: {
          50: '#131318',
          100: '#1c1c24',
          200: '#2b2b36',
          300: '#40404e',
          400: '#71717f',
          500: '#93939f',
          600: '#b4b4c0',
          700: '#d7d7de',
          800: '#eeeef1',
          900: '#f8f8fa',
        },
      },
      keyframes: {
        'pulse-slow': {
          '0%, 100%': { opacity: '0.3' },
          '50%': { opacity: '0.5' },
        },
      },
      animation: {
        'pulse-slow': 'pulse-slow 6s ease-in-out infinite',
      },
    },
  },
  plugins: [],
};
