import { motion } from 'framer-motion';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../../hooks/useAuth';

export function NavBar() {
  const { user, isAuthenticated, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = async () => {
    await logout();
    navigate('/login');
  };

  if (!isAuthenticated) return null;

  return (
    <nav className="sticky top-0 z-10 border-b border-white/10 bg-base/80 backdrop-blur-lg">
      <div className="mx-auto flex max-w-6xl items-center justify-between px-6 py-4">
        <Link
          to="/projects"
          className="bg-gradient-to-r from-violet-400 to-pink-400 bg-clip-text text-lg font-bold italic text-transparent"
        >
          Smart Shorts
        </Link>
        <div className="flex items-center gap-4">
          <Link
            to="/projects/new"
            className="text-sm font-medium text-gray-500 transition-colors hover:text-white"
          >
            New Project
          </Link>
          <Link
            to="/profile"
            className="flex items-center gap-2 text-sm font-medium text-gray-500 transition-colors hover:text-white"
          >
            <span className="flex h-7 w-7 items-center justify-center rounded-full bg-gradient-to-br from-violet-500 to-pink-500 text-xs font-semibold text-white">
              {(user?.full_name ?? user?.email ?? '?').charAt(0).toUpperCase()}
            </span>
            {user?.full_name ?? user?.email}
          </Link>
          <motion.button
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            onClick={() => void handleLogout()}
            className="rounded-full border border-white/10 px-4 py-2 text-sm font-medium text-gray-500 transition-colors hover:border-pink-400/40 hover:text-white"
          >
            Sign out
          </motion.button>
        </div>
      </div>
    </nav>
  );
}
