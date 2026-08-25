"use client";

import React, { useState, useEffect } from "react";
import {
  Activity,
  CheckCircle2,
  AlertCircle,
  RefreshCw,
  Database,
  Server,
  Clock,
  Shield,
  Code2,
} from "lucide-react";
import { api } from "@/lib/api";
import { HealthCheckResponse } from "@/types";
import { cn } from "@/lib/utils";

export default function HealthStatus() {
  const [health, setHealth] = useState<HealthCheckResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [latencyMs, setLatencyMs] = useState<number | null>(null);
  const [showRaw, setShowRaw] = useState<boolean>(false);

  const fetchHealth = async () => {
    setLoading(true);
    setError(null);
    const start = performance.now();
    try {
      const data = await api.getHealth();
      const end = performance.now();
      setLatencyMs(Math.round(end - start));
      setHealth(data);
    } catch (err: any) {
      setError(
        err.message || "Failed to reach DemandIQ backend service on port 8000."
      );
      setHealth(null);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchHealth();
  }, []);

  const isHealthy = health?.status === "healthy";

  return (
    <div className="bg-white rounded-2xl border border-slate-200/80 shadow-elevation p-6 sm:p-8">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-6 border-b border-slate-100">
        <div className="flex items-center gap-3.5">
          <div
            className={cn(
              "w-12 h-12 rounded-xl flex items-center justify-center shadow-md",
              isHealthy
                ? "bg-emerald-50 text-emerald-600 border border-emerald-200/80"
                : error
                ? "bg-rose-50 text-rose-600 border border-rose-200/80"
                : "bg-amber-50 text-amber-600 border border-amber-200/80"
            )}
          >
            {isHealthy ? (
              <CheckCircle2 className="w-6 h-6" />
            ) : error ? (
              <AlertCircle className="w-6 h-6" />
            ) : (
              <Activity className="w-6 h-6 animate-pulse" />
            )}
          </div>
          <div>
            <div className="flex items-center gap-2.5">
              <h2 className="text-xl font-bold text-slate-900">
                End-to-End System Health
              </h2>
              <span
                className={cn(
                  "text-xs px-2.5 py-0.5 rounded-full font-bold uppercase tracking-wider font-mono border",
                  isHealthy
                    ? "bg-emerald-500/10 text-emerald-700 border-emerald-300"
                    : error
                    ? "bg-rose-500/10 text-rose-700 border-rose-300"
                    : "bg-amber-500/10 text-amber-700 border-amber-300"
                )}
              >
                {loading ? "CHECKING..." : isHealthy ? "ONLINE (200 OK)" : "OFFLINE"}
              </span>
            </div>
            <p className="text-xs text-slate-500 mt-1">
              Frontend Client ⇄ FastAPI (Uvicorn:8000) ⇄ Database
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={() => setShowRaw(!showRaw)}
            className="text-xs font-semibold px-3 py-2 rounded-lg border border-slate-200 text-slate-600 hover:bg-slate-50 transition-colors flex items-center gap-1.5"
          >
            <Code2 className="w-3.5 h-3.5" />
            {showRaw ? "Hide Raw JSON" : "View Raw JSON"}
          </button>
          <button
            onClick={fetchHealth}
            disabled={loading}
            className="text-xs font-semibold px-3.5 py-2 rounded-lg bg-brand-700 text-white hover:bg-brand-800 disabled:opacity-50 transition-colors flex items-center gap-1.5 shadow-sm"
          >
            <RefreshCw className={cn("w-3.5 h-3.5", loading && "animate-spin")} />
            Re-test Connectivity
          </button>
        </div>
      </div>

      {/* Error state alert */}
      {error && (
        <div className="mt-6 p-4 rounded-xl bg-rose-50 border border-rose-200 text-rose-900 text-xs flex items-start gap-3">
          <AlertCircle className="w-5 h-5 text-rose-600 shrink-0 mt-0.5" />
          <div>
            <p className="font-bold text-sm">Backend Connectivity Error</p>
            <p className="mt-1 font-mono text-[11px] bg-rose-100/70 p-2 rounded border border-rose-200/60">
              {error}
            </p>
            <p className="mt-2 text-rose-700">
              Tip: Ensure the FastAPI server is running with{" "}
              <code className="bg-white px-1.5 py-0.5 rounded font-mono text-slate-800 border">
                uvicorn app.main:app --reload --port 8000
              </code>
            </p>
          </div>
        </div>
      )}

      {/* Grid of Diagnostics Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mt-6">
        {/* Backend Service Card */}
        <div className="p-4 rounded-xl bg-slate-50 border border-slate-200/80">
          <div className="flex items-center justify-between text-slate-500 mb-2">
            <span className="text-xs font-semibold uppercase tracking-wider font-mono">
              API Service
            </span>
            <Server className="w-4 h-4 text-brand-600" />
          </div>
          <div className="font-bold text-slate-800 text-sm">
            {health?.service || "DemandIQ Backend"}
          </div>
          <div className="text-xs text-slate-500 mt-1 flex items-center gap-1.5">
            <span className="font-mono">v{health?.version || "1.0.0"}</span>
            <span>•</span>
            <span className="capitalize">{health?.environment || "development"}</span>
          </div>
        </div>

        {/* Database Status Card */}
        <div className="p-4 rounded-xl bg-slate-50 border border-slate-200/80">
          <div className="flex items-center justify-between text-slate-500 mb-2">
            <span className="text-xs font-semibold uppercase tracking-wider font-mono">
              Database
            </span>
            <Database className="w-4 h-4 text-tealAccent-600" />
          </div>
          <div className="font-bold text-slate-800 text-sm flex items-center gap-1.5">
            <span
              className={cn(
                "w-2 h-2 rounded-full",
                health?.database?.includes("connected")
                  ? "bg-emerald-500"
                  : "bg-rose-500"
              )}
            ></span>
            <span className="capitalize">{health?.database || "Checking..."}</span>
          </div>
          <div className="text-xs text-slate-500 mt-1">
            PostgreSQL / SQLAlchemy
          </div>
        </div>

        {/* Roundtrip Latency */}
        <div className="p-4 rounded-xl bg-slate-50 border border-slate-200/80">
          <div className="flex items-center justify-between text-slate-500 mb-2">
            <span className="text-xs font-semibold uppercase tracking-wider font-mono">
              API Latency
            </span>
            <Activity className="w-4 h-4 text-brand-500" />
          </div>
          <div className="font-bold text-slate-800 text-sm font-mono">
            {latencyMs !== null ? `${latencyMs} ms` : "—"}
          </div>
          <div className="text-xs text-emerald-600 font-medium mt-1">
            {latencyMs && latencyMs < 100 ? "Optimal Response" : "Normal"}
          </div>
        </div>

        {/* Uptime */}
        <div className="p-4 rounded-xl bg-slate-50 border border-slate-200/80">
          <div className="flex items-center justify-between text-slate-500 mb-2">
            <span className="text-xs font-semibold uppercase tracking-wider font-mono">
              Uptime
            </span>
            <Clock className="w-4 h-4 text-amber-500" />
          </div>
          <div className="font-bold text-slate-800 text-sm font-mono">
            {health?.uptime_seconds ? `${health.uptime_seconds}s` : "Active"}
          </div>
          <div className="text-xs text-slate-500 mt-1">
            Continuous operation
          </div>
        </div>
      </div>

      {/* Raw JSON View */}
      {showRaw && health && (
        <div className="mt-6">
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs font-semibold text-slate-600 font-mono">
              Raw Response from GET /health
            </span>
          </div>
          <pre className="p-4 rounded-xl bg-slate-900 text-tealAccent-300 font-mono text-xs overflow-x-auto border border-slate-800">
            {JSON.stringify(health, null, 2)}
          </pre>
        </div>
      )}
    </div>
  );
}
