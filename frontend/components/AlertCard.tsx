import React from "react";
import { AlertCircle, AlertTriangle, Info, CheckCircle2 } from "lucide-react";
import { Alert } from "@/types";
import { cn } from "@/lib/utils";

interface AlertCardProps {
  alert: Alert;
  onResolve?: (id: number) => void;
}

export default function AlertCard({ alert, onResolve }: AlertCardProps) {
  const sevKey = alert.severity?.toLowerCase() || "info";

  const severityConfig = {
    critical: {
      bg: "bg-rose-50/80 border-rose-200 text-rose-950",
      badge: "bg-rose-100 text-rose-800 border-rose-300",
      icon: AlertCircle,
      iconColor: "text-rose-600",
    },
    warning: {
      bg: "bg-amber-50/80 border-amber-200 text-amber-950",
      badge: "bg-amber-100 text-amber-800 border-amber-300",
      icon: AlertTriangle,
      iconColor: "text-amber-600",
    },
    info: {
      bg: "bg-sky-50/80 border-sky-200 text-sky-950",
      badge: "bg-sky-100 text-sky-800 border-sky-300",
      icon: Info,
      iconColor: "text-sky-600",
    },
  };

  const config =
    severityConfig[sevKey as keyof typeof severityConfig] || severityConfig.info;
  const Icon = config.icon;

  return (
    <div
      className={cn(
        "p-4 rounded-xl border flex items-start justify-between gap-4 transition-all duration-200 shadow-sm",
        config.bg
      )}
    >
      <div className="flex items-start gap-3">
        <div className="p-1.5 rounded-lg bg-white shadow-xs shrink-0 mt-0.5">
          <Icon className={cn("w-5 h-5", config.iconColor)} />
        </div>
        <div>
          <div className="flex items-center gap-2">
            <span
              className={cn(
                "text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded border font-mono",
                config.badge
              )}
            >
              {alert.severity}
            </span>
            <span className="text-[10px] font-semibold uppercase px-2 py-0.5 rounded bg-slate-100 text-slate-700 font-mono">
              {alert.type}
            </span>
            <span className="text-[11px] text-slate-500 font-medium">
              {new Date(alert.created_at).toLocaleDateString()}
            </span>
          </div>
          <p className="text-xs text-slate-700 mt-2 leading-relaxed">{alert.message}</p>
        </div>
      </div>

      {alert.status !== "acknowledged" && onResolve && (
        <button
          onClick={() => onResolve(alert.id)}
          className="shrink-0 text-xs px-3 py-1.5 rounded-lg bg-white border border-slate-200 hover:bg-slate-50 text-slate-700 font-medium shadow-xs transition-colors flex items-center gap-1.5"
        >
          <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
          Acknowledge
        </button>
      )}
    </div>
  );
}
