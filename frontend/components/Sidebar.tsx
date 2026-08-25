"use client";

import React from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  LayoutDashboard,
  TrendingUp,
  Boxes,
  BellRing,
  FileBarChart2,
  Settings,
  Activity,
  Sparkles,
  Zap,
  Shield,
  Building2,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { useAuth } from "@/context/AuthContext";

export default function Sidebar() {
  const pathname = usePathname();
  const { user } = useAuth();

  const navigationItems = [
    { name: "System Readiness", href: "/", icon: Activity },
    { name: "Executive Dashboard", href: "/dashboard", icon: LayoutDashboard },
    { name: "Demand Forecasts", href: "/forecasts", icon: TrendingUp },
    { name: "Inventory Reorder", href: "/inventory", icon: Boxes },
    { name: "Risk Alerts", href: "/alerts", icon: BellRing, badge: "3" },
    { name: "Reports & What-If", href: "/reports", icon: FileBarChart2 },
    { name: "Dataset Explorer", href: "/explorer", icon: Database },
    { name: "Settings & Ingestion", href: "/settings", icon: Settings },
  ];

  return (
    <aside className="w-64 bg-slate-900 border-r border-slate-800 flex flex-col shrink-0 text-slate-200 select-none">
      {/* Brand Header */}
      <div className="h-16 px-6 flex items-center gap-3 border-b border-slate-800/80 bg-slate-950/40">
        <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-brand-700 via-tealAccent-500 to-tealAccent-300 flex items-center justify-center shadow-lg shadow-tealAccent-500/20 ring-1 ring-white/20">
          <Zap className="w-5 h-5 text-white fill-white" />
        </div>
        <div>
          <div className="flex items-center gap-1.5">
            <span className="font-bold text-lg tracking-tight text-white font-sans">
              Demand<span className="text-tealAccent-400">IQ</span>
            </span>
            <span className="text-[10px] font-semibold uppercase px-1.5 py-0.5 rounded bg-tealAccent-900/60 text-tealAccent-300 border border-tealAccent-700/50">
              v1.0
            </span>
          </div>
          <p className="text-[11px] text-slate-400">Intelligent Retail AI</p>
        </div>
      </div>

      {/* User / Role Badge */}
      {user && (
        <div className="px-4 py-3 mx-3 my-2 rounded-xl bg-slate-800/40 border border-slate-800 flex items-center justify-between">
          <div className="flex items-center gap-2.5 overflow-hidden">
            <div className="w-7 h-7 rounded-full bg-teal-500/20 border border-teal-500/40 flex items-center justify-center text-teal-300 font-bold text-xs shrink-0">
              {user.name.charAt(0).toUpperCase()}
            </div>
            <div className="overflow-hidden">
              <p className="text-xs font-semibold text-white truncate">{user.name}</p>
              <div className="flex items-center gap-1 text-[10px] text-slate-400">
                <Shield className="w-2.5 h-2.5 text-teal-400" />
                <span className="uppercase font-mono tracking-wider">{user.role.replace("_", " ")}</span>
              </div>
            </div>
          </div>
          {user.assigned_store_id && (
            <span className="text-[10px] px-2 py-0.5 rounded bg-amber-500/10 border border-amber-500/30 text-amber-300 font-mono flex items-center gap-1">
              <Building2 className="w-2.5 h-2.5" />
              S{user.assigned_store_id}
            </span>
          )}
        </div>
      )}

      {/* Navigation List */}
      <div className="flex-1 py-4 px-3 space-y-1.5 overflow-y-auto">
        <div className="px-3 pb-2 text-[10px] font-semibold uppercase tracking-wider text-slate-400">
          Core Modules
        </div>
        {navigationItems.map((item) => {
          const isActive = pathname === item.href;
          const Icon = item.icon;
          return (
            <Link
              key={item.name}
              href={item.href}
              className={cn(
                "flex items-center justify-between px-3 py-2.5 rounded-lg text-sm font-medium transition-all duration-150 group",
                isActive
                  ? "bg-brand-700/60 text-white shadow-sm ring-1 ring-tealAccent-500/30 border-l-2 border-tealAccent-400"
                  : "text-slate-400 hover:text-slate-100 hover:bg-slate-800/60"
              )}
            >
              <div className="flex items-center gap-3">
                <Icon
                  className={cn(
                    "w-4 h-4 transition-colors",
                    isActive ? "text-tealAccent-400" : "text-slate-400 group-hover:text-slate-200"
                  )}
                />
                <span>{item.name}</span>
              </div>
              {item.badge && (
                <span className="text-xs px-2 py-0.5 rounded-full bg-rose-500/20 text-rose-300 font-semibold border border-rose-500/30">
                  {item.badge}
                </span>
              )}
            </Link>
          );
        })}
      </div>

      {/* Forecasting Model Status Card in Sidebar */}
      <div className="p-4 m-3 rounded-xl bg-gradient-to-b from-slate-800/80 to-slate-900/90 border border-slate-700/60 text-xs shadow-inner">
        <div className="flex items-center justify-between mb-2">
          <span className="flex items-center gap-1.5 font-medium text-slate-300">
            <Sparkles className="w-3.5 h-3.5 text-tealAccent-400" />
            Ensemble AI Engine
          </span>
          <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
        </div>
        <p className="text-slate-400 text-[11px] leading-relaxed mb-3">
          Prophet + XGBoost weighted model active with 94.2% accuracy.
        </p>
        <div className="w-full bg-slate-950/60 rounded-full h-1.5 overflow-hidden">
          <div className="bg-gradient-to-r from-brand-500 to-tealAccent-400 h-1.5 rounded-full w-[94%]"></div>
        </div>
      </div>
    </aside>
  );
}
