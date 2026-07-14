"use client";

import { AlertTriangle, Inbox, RefreshCw } from "lucide-react";

export function Skeleton({ className = "" }: { className?: string }) {
  return <div className={`animate-pulse rounded-xl bg-mist ${className}`} />;
}

export function ChartSkeleton() {
  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <Skeleton className="h-3 w-24" />
        <Skeleton className="h-3 w-12" />
      </div>
      <Skeleton className="h-40 w-full rounded-2xl" />
    </div>
  );
}

export function EmptyState({
  label = "No data yet",
  hint = "Data will appear here once collection begins.",
}: {
  label?: string;
  hint?: string;
}) {
  return (
    <div className="flex flex-col items-center justify-center text-center py-10 h-full">
      <div className="w-11 h-11 rounded-2xl bg-mist flex items-center justify-center mb-3">
        <Inbox size={18} className="text-gray-400" />
      </div>
      <p className="text-sm font-semibold text-ink">{label}</p>
      <p className="text-xs text-gray-400 mt-1 max-w-[220px]">{hint}</p>
    </div>
  );
}

export function ErrorState({
  label = "Couldn't load data",
  hint = "Check the connection and try again.",
  onRetry,
}: {
  label?: string;
  hint?: string;
  onRetry?: () => void;
}) {
  return (
    <div className="flex flex-col items-center justify-center text-center py-10 h-full">
      <div className="w-11 h-11 rounded-2xl bg-danger/10 flex items-center justify-center mb-3">
        <AlertTriangle size={18} className="text-danger" />
      </div>
      <p className="text-sm font-semibold text-ink">{label}</p>
      <p className="text-xs text-gray-400 mt-1 max-w-[220px]">{hint}</p>
      {onRetry && (
        <button
          onClick={onRetry}
          className="mt-4 inline-flex items-center gap-1.5 px-4 py-2 rounded-full border border-gray-200 text-xs font-semibold text-ink hover:bg-mist/60 transition-colors"
        >
          <RefreshCw size={12} />
          Retry
        </button>
      )}
    </div>
  );
}
