export default function SocialButtons() {
  return (
    <div className="grid grid-cols-2 gap-3">
      <button
        type="button"
        className="flex items-center justify-center gap-2.5 py-3 px-4 rounded-full border border-gray-200 text-sm font-semibold text-ink hover:bg-mist/60 transition-colors"
      >
        <svg width="18" height="18" viewBox="0 0 24 24">
          <path fill="#4285F4" d="M23.52 12.27c0-.85-.08-1.67-.22-2.45H12v4.64h6.47a5.53 5.53 0 01-2.4 3.63v3h3.87c2.27-2.09 3.58-5.17 3.58-8.82z" />
          <path fill="#34A853" d="M12 24c3.24 0 5.96-1.07 7.94-2.91l-3.87-3c-1.08.72-2.45 1.15-4.07 1.15-3.13 0-5.78-2.11-6.73-4.95H1.28v3.1A12 12 0 0012 24z" />
          <path fill="#FBBC05" d="M5.27 14.29a7.2 7.2 0 010-4.58v-3.1H1.28a12 12 0 000 10.78z" />
          <path fill="#EA4335" d="M12 4.75c1.77 0 3.35.61 4.6 1.8l3.42-3.42C17.95 1.19 15.24 0 12 0A12 12 0 001.28 6.61l3.99 3.1C6.22 6.86 8.87 4.75 12 4.75z" />
        </svg>
        Google
      </button>
      <button
        type="button"
        className="flex items-center justify-center gap-2.5 py-3 px-4 rounded-full border border-gray-200 text-sm font-semibold text-ink hover:bg-mist/60 transition-colors"
      >
        <svg width="16" height="16" viewBox="0 0 23 23">
          <rect x="1" y="1" width="10" height="10" fill="#F25022" />
          <rect x="12" y="1" width="10" height="10" fill="#7FBA00" />
          <rect x="1" y="12" width="10" height="10" fill="#00A4EF" />
          <rect x="12" y="12" width="10" height="10" fill="#FFB900" />
        </svg>
        Microsoft
      </button>
    </div>
  );
}
