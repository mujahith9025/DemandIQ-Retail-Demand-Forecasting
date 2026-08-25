"use client";

import React, { ReactNode } from "react";
import { Sparkles } from "lucide-react";

interface ChartWrapperProps {
  title: string;
  subtitle?: string;
  badge?: string;
  children: ReactNode;
  headerAction?: ReactNode;
  heightClass?: string;
}

export default function ChartWrapper({
  title,
  subtitle,
  badge,
  children,
  headerAction,
  heightClass = "h-80",
}: ChartWrapperProps) {
  return (
    <div className="bg-white rounded-xl border border-slate-200/80 p-6 shadow-sm flex flex-col justify-between">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 mb-6">
        <div>
          <div className="flex items-center gap-2">
            <h3 className="font-bold text-slate-900 text-base">{title}</h3>
            {badge && (
              <span className="inline-flex items-center gap-1 text-[11px] font-semibold px-2 py-0.5 rounded-full bg-tealAccent-50 text-tealAccent-700 border border-tealAccent-200">
                <Sparkles className="w-3 h-3 text-tealAccent-500" />
                {badge}
              </span>
            )}
          </div>
          {subtitle && (
            <p className="text-xs text-slate-500 mt-0.5">{subtitle}</p>
          )}
        </div>
        {headerAction && <div>{headerAction}</div>}
      </div>

      <div className={`w-full ${heightClass} relative`}>
        {children}
      </div>
    </div>
  );
}
