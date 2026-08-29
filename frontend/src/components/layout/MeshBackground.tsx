export function MeshBackground() {
  return (
    <div className="fixed inset-0 -z-10 overflow-hidden" aria-hidden="true">
      <div className="absolute inset-0 bg-gradient-to-br from-base via-base-raised to-base" />
      <div className="absolute top-0 left-1/4 h-96 w-96 rounded-full bg-violet-600 opacity-20 blur-3xl animate-pulse-slow" />
      <div className="absolute bottom-0 right-1/4 h-96 w-96 rounded-full bg-pink-600 opacity-20 blur-3xl animate-pulse-slow" />
      <div className="absolute top-1/3 right-1/3 h-72 w-72 rounded-full bg-indigo-600 opacity-10 blur-3xl animate-pulse-slow" />
    </div>
  );
}
