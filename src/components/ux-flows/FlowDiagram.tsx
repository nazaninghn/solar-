import { ArrowRight, Check, X } from "lucide-react";
import type { Flow } from "./data";

function isBranch(step: Flow["steps"][number]): step is { branch: string[] } {
  return "branch" in step;
}

export default function FlowDiagram({ flow }: { flow: Flow }) {
  return (
    <div className="rounded-3xl bg-white border border-gray-100 p-6">
      <div className="flex flex-wrap items-start justify-between gap-3 mb-5">
        <div>
          <div className="flex items-center gap-2">
            <span className="text-[11px] font-mono text-gray-300">FLOW {flow.number}</span>
            {flow.status === "live" ? (
              <span className="text-[10px] font-bold uppercase tracking-wide px-2 py-0.5 rounded-full bg-primary-green/10 text-primary-green">Live</span>
            ) : (
              <span className="text-[10px] font-bold uppercase tracking-wide px-2 py-0.5 rounded-full bg-mist text-gray-500">Planned</span>
            )}
          </div>
          <h4 className="text-sm font-semibold text-ink mt-1">{flow.title}</h4>
        </div>
        {flow.route && (
          <a href={flow.route} className="text-xs font-semibold text-lime-dark hover:underline shrink-0">
            View live →
          </a>
        )}
      </div>

      <div className="flex flex-wrap items-center gap-y-3">
        {flow.steps.map((step, i) => (
          <div key={i} className="flex items-center">
            {i > 0 && <ArrowRight size={14} className="text-gray-300 mx-1.5 shrink-0" />}
            {isBranch(step) ? (
              <div className="flex items-center gap-2">
                <div className="flex items-center gap-1.5 px-3 py-2 rounded-xl bg-primary-green/10 text-primary-green text-xs font-semibold">
                  <Check size={12} />
                  {step.branch[0]}
                </div>
                <span className="text-[10px] text-gray-300">or</span>
                <div className="flex items-center gap-1.5 px-3 py-2 rounded-xl bg-danger/10 text-danger text-xs font-semibold">
                  <X size={12} />
                  {step.branch[1]}
                </div>
              </div>
            ) : (
              <div className="px-3 py-2 rounded-xl bg-warm-bg text-ink text-xs font-medium whitespace-nowrap">
                {step.label}
              </div>
            )}
          </div>
        ))}
      </div>

      {flow.note && (
        <p className="text-xs text-gray-400 mt-4 pt-4 border-t border-gray-50 leading-relaxed">{flow.note}</p>
      )}
    </div>
  );
}
