import React from "react";
import { TrendingUp, TrendingDown, Minus, LucideIcon } from "lucide-react";
import { cn } from "@/lib/utils";

interface KPICardProps {
  title: string;
  value: string | number;
  change?: string;
  trend?: "up" | "down" | "neutral";
  subtitle?: string;
  icon: LucideIcon;
  badgeColor?: "brand" | "teal" | "emerald" | "amber" | "rose";
}

export default function KPICard({
  title,
  value,
  change,
  trend = "neutral",
  subtitle,
  icon: Icon,
  badgeColor = "brand",
}: KPICardProps) {
  const colorMap = {
    brand: "bg-brand-50 text-brand-700 border-brand-200/60",
    teal: "bg-tealAccent-50 text-tealAccent-700 border-tealAccent-200/60",
    emerald: "bg-emerald-50 text-emerald-700 border-emerald-200/60",
    amber: "bg-amber-50 text-amber-700 border-amber-200/60",
    rose: "bg-rose-50 text-rose-700 border-rose-200/60",
  };

  return (
    <div className="bg-white rounded-xl border border-slate-200/80 p-5 shadow-sm hover:shadow-md transition-all duration-200 flex flex-col justify-between">
      <div className="flex items-start justify-between">
        <div>
          <p className="text-xs font-semibold uppercase tracking-wider text-slate-400 font-mono">
            {title}
          </p>
          <h3 className="text-2xl font-bold text-slate-900 mt-1 tracking-tight">
            {value}
          </h3>
        </div>
        <div className={cn("p-2.5 rounded-xl border", colorMap[badgeColor])}>
          <Icon className="w-5 h-5" />
        </div>
      </div>

      <div className="mt-4 pt-3 border-t border-slate-100 flex items-center justify-between text-xs">
        {change && (
          <div className="flex items-center gap-1 font-medium">
            {trend === "up" && (
              <span className="flex items-center text-emerald-600">
                <TrendingUp className="w-3.5 h-3.5 mr-0.5" />
                {change}
              </span>
            )}
            {trend === "down" && (
              <span className="flex items-center text-rose-600">
                <TrendingDown className="w-3.5 h-3.5 mr-0.5" />
                {change}
              </span>
            )}
            {trend === "neutral" && (
              <span className="flex items-center text-slate-500">
                <Minus className="w-3.5 h-3.5 mr-0.5" />
                {change}
              </span>
            )}
            <span className="text-slate-400 font-normal ml-1">vs last period</span>
          </div>
        )}
        {subtitle && !change && (
          <span className="text-slate-400">{subtitle}</span>
        )}
      </div>
    </div>
  );
}
