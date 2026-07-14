"use client";

import { MoreHorizontal } from "lucide-react";
import { ChartSkeleton, EmptyState, ErrorState } from "./States";

export type ChartCardStatus = "ready" | "loading" | "empty" | "error";

export default function ChartCard({
  title,
  subtitle,
  tag,
  status = "ready",
  actions,
  children,
  className = "",
  height = "h-64",
}: {
  title: string;
  subtitle?: string;
  tag?: string;
  status?: ChartCardStatus;
  actions?: React.ReactNode;
  children: React.ReactNode;
  className?: string;
  height?: string;
}) {
  return (
    <div
      className={`group rounded-3xl bg-white border border-gray-100 p-6 hover:border-gray-200 hover:shadow-md transition-all ${className}`}
    >
      <div className="flex items-start justify-between gap-3 mb-4">
        <div>
          <div className="flex items-center gap-2">
            <h4 className="text-sm font-semibold text-ink">{title}</h4>
            {tag && (
              <span className="text-[10px] font-mono text-gray-300 group-hover:text-gray-400 transition-colors">{tag}</span>
            )}
          </div>
          {subtitle && <p className="text-xs text-gray-400 mt-0.5">{subtitle}</p>}
        </div>
        <div className="flex items-center gap-2 shrink-0">
          {actions}
          <button className="text-gray-300 hover:text-ink opacity-0 group-hover:opacity-100 transition-opacity" aria-label="More options">
            <MoreHorizontal size={16} />
          </button>
        </div>
      </div>

      <div className={status === "ready" ? height : ""}>
        {status === "loading" && <ChartSkeleton />}
        {status === "empty" && <EmptyState />}
        {status === "error" && <ErrorState />}
        {status === "ready" && children}
      </div>
    </div>
  );
}
