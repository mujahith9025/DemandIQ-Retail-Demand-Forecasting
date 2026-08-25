import React from "react";
import Link from "next/link";
import {
  Boxes,
  TrendingUp,
  BellRing,
  FileBarChart2,
  Settings,
  ArrowRight,
  Database,
  Server,
  Layers,
  Sparkles,
} from "lucide-react";
import HealthStatus from "@/components/HealthStatus";

export default function HomePage() {
  const modules = [
    {
      title: "Executive Dashboard",
      desc: "Top-line retail KPIs, forecast accuracy tracking, and 30-day projected revenue.",
      href: "/dashboard",
      icon: Layers,
      color: "bg-brand-50 text-brand-700 border-brand-200",
    },
    {
      title: "Demand Forecasts",
      desc: "SKU-level LightGBM predictions with 95% confidence intervals and season indicators.",
      href: "/forecasts",
      icon: TrendingUp,
      color: "bg-tealAccent-50 text-tealAccent-700 border-tealAccent-200",
    },
    {
      title: "Inventory & Reorder",
      desc: "Real-time stock on hand, lead times, safety stocks, and automated reorder points.",
      href: "/inventory",
      icon: Boxes,
      color: "bg-emerald-50 text-emerald-700 border-emerald-200",
    },
    {
      title: "Risk & Anomaly Alerts",
      desc: "Early warning system for stockout risks, sudden demand spikes, and overstock flags.",
      href: "/alerts",
      icon: BellRing,
      color: "bg-rose-50 text-rose-700 border-rose-200",
    },
  ];

  return (
    <div className="space-y-8 pb-12">
      {/* Welcome Banner */}
      <div className="rounded-3xl bg-gradient-to-r from-slate-900 via-brand-900 to-slate-900 p-8 text-white relative overflow-hidden shadow-elevation border border-slate-800">
        <div className="absolute top-0 right-0 -mt-8 -mr-8 w-64 h-64 bg-tealAccent-500/10 rounded-full blur-3xl pointer-events-none"></div>
        <div className="relative z-10 max-w-2xl">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-tealAccent-500/10 border border-tealAccent-400/20 text-tealAccent-300 text-xs font-semibold uppercase tracking-wider mb-4 font-mono">
            <Sparkles className="w-3.5 h-3.5" />
            DemandIQ Foundation Ready
          </div>
          <h1 className="text-3xl sm:text-4xl font-extrabold tracking-tight">
            Intelligent Retail Demand Forecasting
          </h1>
          <p className="mt-3 text-slate-300 text-sm sm:text-base leading-relaxed">
            Foundational architecture successfully scaffolded: FastAPI backend,
            Next.js 14 frontend, PostgreSQL ORM models, and live end-to-end
            health telemetry.
          </p>
        </div>
      </div>

      {/* Live Health Status Widget */}
      <section>
        <HealthStatus />
      </section>

      {/* Scaffolded Modules Quick Access */}
      <section className="space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-lg font-bold text-slate-900">Platform Modules</h3>
            <p className="text-xs text-slate-500">
              Scaffolded routes ready for business logic and model pipelines
            </p>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {modules.map((mod) => {
            const Icon = mod.icon;
            return (
              <Link
                key={mod.title}
                href={mod.href}
                className="p-6 rounded-2xl bg-white border border-slate-200/80 shadow-sm hover:shadow-md hover:border-brand-300 transition-all duration-200 group flex flex-col justify-between"
              >
                <div className="flex items-start justify-between gap-4">
                  <div className="space-y-2">
                    <div className="flex items-center gap-3">
                      <div className={`p-2.5 rounded-xl border ${mod.color}`}>
                        <Icon className="w-5 h-5" />
                      </div>
                      <h4 className="font-bold text-slate-900 text-base group-hover:text-brand-700 transition-colors">
                        {mod.title}
                      </h4>
                    </div>
                    <p className="text-xs text-slate-500 leading-relaxed pl-1">
                      {mod.desc}
                    </p>
                  </div>
                  <ArrowRight className="w-4 h-4 text-slate-300 group-hover:text-brand-600 group-hover:translate-x-1 transition-all mt-3 shrink-0" />
                </div>
              </Link>
            );
          })}
        </div>
      </section>
    </div>
  );
}
