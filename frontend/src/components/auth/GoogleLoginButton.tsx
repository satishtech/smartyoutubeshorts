import { motion } from 'framer-motion';
import { getGoogleLoginUrl } from '../../services/authService';

export function GoogleLoginButton() {
  const handleClick = () => {
    window.location.href = getGoogleLoginUrl();
  };

  return (
    <motion.button
      type="button"
      onClick={handleClick}
      whileHover={{ scale: 1.02, y: -2 }}
      whileTap={{ scale: 0.98 }}
      className="flex w-full items-center justify-center gap-3 rounded-full border-2 border-slate-200 bg-white px-6 py-3 font-semibold text-slate-700 shadow-sm hover:shadow-md"
    >
      <svg className="h-5 w-5" viewBox="0 0 24 24" aria-hidden="true">
        <path
          fill="#4285F4"
          d="M23.49 12.27c0-.79-.07-1.54-.19-2.27H12v4.51h6.47c-.29 1.48-1.14 2.73-2.42 3.58v2.98h3.91c2.29-2.11 3.53-5.22 3.53-8.8z"
        />
        <path
          fill="#34A853"
          d="M12 24c3.24 0 5.95-1.08 7.93-2.93l-3.91-2.98c-1.08.72-2.47 1.15-4.02 1.15-3.09 0-5.71-2.09-6.64-4.9H1.32v3.07C3.29 21.3 7.31 24 12 24z"
        />
        <path
          fill="#FBBC05"
          d="M5.36 14.34A7.2 7.2 0 0 1 5 12c0-.81.14-1.6.36-2.34V6.59H1.32A11.98 11.98 0 0 0 0 12c0 1.93.46 3.76 1.32 5.41l4.04-3.07z"
        />
        <path
          fill="#EA4335"
          d="M12 4.75c1.76 0 3.34.61 4.58 1.79l3.44-3.44C17.94 1.19 15.24 0 12 0 7.31 0 3.29 2.7 1.32 6.59l4.04 3.07C6.29 6.84 8.91 4.75 12 4.75z"
        />
      </svg>
      Continue with Google
    </motion.button>
  );
}
