"use client";

import React, { useState, useEffect } from "react";
import { BellRing, CheckCheck, RefreshCw, AlertCircle, AlertTriangle, Info, CheckCircle2, X } from "lucide-react";
import { api } from "@/lib/api";
import { Alert } from "@/types";
import { useToast } from "@/context/ToastContext";
import { cn } from "@/lib/utils";

export default function AlertsPage() {
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [severityFilter, setSeverityFilter] = useState<string>("all");
  const [statusFilter, setStatusFilter] = useState<string>("new");

  const toast = useToast();

  const fetchAlerts = async () => {
    setLoading(true);
    try {
      const res = await api.alerts.getAlerts(severityFilter, statusFilter, 50, 0);
      setAlerts(res.items || []);
    } catch (err: any) {
      toast.error(err.message || "Failed to load alerts.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAlerts();
    // Real-time polling every 12 seconds
    const interval = setInterval(fetchAlerts, 12000);
    return () => clearInterval(interval);
  }, [severityFilter, statusFilter]);

  const handleUpdateStatus = async (id: number, newStatus: "acknowledged" | "dismissed") => {
    try {
      await api.alerts.patchAlert(id, newStatus);
      toast.success(`Alert marked as ${newStatus}.`, "Status Updated");

      // Optimistic update
      setAlerts((prev) =>
        prev.map((a) => (a.id === id ? { ...a, status: newStatus } : a)).filter((a) =>
          statusFilter === "all" ? true : a.status === statusFilter
        )
      );
    } catch (err: any) {
      toast.error(err.message || "Failed to update alert status.");
    }
  };

  const handleAcknowledgeAll = async () => {
    try {
      for (const alert of alerts) {
        if (alert.status === "new") {
          await api.alerts.patchAlert(alert.id, "acknowledged");
        }
      }
      toast.success("All active alerts acknowledged.", "Action Complete");
      fetchAlerts();
    } catch (err: any) {
      toast.error(err.message || "Failed to acknowledge alerts.");
    }
  };

  const getSeverityStyle = (sev: string) => {
    switch (sev.toLowerCase()) {
      case "critical":
        return {
          bg: "bg-rose-50/80 border-rose-200 text-rose-950",
          badge: "bg-rose-100 text-rose-800 border-rose-300",
          icon: AlertCircle,
          iconColor: "text-rose-600",
        };
      case "warning":
        return {
          bg: "bg-amber-50/80 border-amber-200 text-amber-950",
          badge: "bg-amber-100 text-amber-800 border-amber-300",
          icon: AlertTriangle,
          iconColor: "text-amber-600",
        };
      default:
        return {
          bg: "bg-sky-50/80 border-sky-200 text-sky-950",
          badge: "bg-sky-100 text-sky-800 border-sky-300",
          icon: Info,
          iconColor: "text-sky-600",
        };
    }
  };

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">Risk & Anomaly Alerts</h1>
          <p className="text-xs text-slate-500 mt-1">
            Automated intelligence alerts for inventory shortages, demand shocks, and replenishment bottlenecks.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={fetchAlerts}
            title="Poll Now"
            className="p-2 bg-white border border-slate-200 hover:bg-slate-50 rounded-xl text-slate-600 shadow-2xs"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? "animate-spin text-teal-600" : ""}`} />
          </button>

          <button
            onClick={handleAcknowledgeAll}
            disabled={alerts.length === 0}
            className="px-4 py-2.5 rounded-xl border border-slate-200 bg-white hover:bg-slate-50 text-slate-700 text-xs font-semibold flex items-center gap-2 transition-colors disabled:opacity-50 shadow-2xs"
          >
            <CheckCheck className="w-4 h-4 text-slate-500" />
            <span>Acknowledge All</span>
          </button>
        </div>
      </div>

      {/* Filter Chips Ribbon */}
      <div className="p-4 rounded-2xl bg-white border border-slate-200/80 shadow-xs flex flex-wrap items-center justify-between gap-4 text-xs">
        {/* Severity Filters */}
        <div className="flex items-center gap-2">
          <span className="font-semibold text-slate-500 font-mono text-[11px] uppercase">Severity:</span>
          <div className="flex items-center p-1 bg-slate-100 rounded-xl">
            {["all", "critical", "warning", "info"].map((sev) => (
              <button
                key={sev}
                onClick={() => setSeverityFilter(sev)}
                className={`px-3 py-1.5 rounded-lg font-semibold uppercase font-mono transition-colors ${
                  severityFilter === sev ? "bg-white text-slate-900 shadow-2xs" : "text-slate-500 hover:text-slate-900"
                }`}
              >
                {sev}
              </button>
            ))}
          </div>
        </div>

        {/* Status Filters */}
        <div className="flex items-center gap-2">
          <span className="font-semibold text-slate-500 font-mono text-[11px] uppercase">Status:</span>
          <div className="flex items-center p-1 bg-slate-100 rounded-xl">
            {["new", "acknowledged", "all"].map((st) => (
              <button
                key={st}
                onClick={() => setStatusFilter(st)}
                className={`px-3 py-1.5 rounded-lg font-semibold uppercase font-mono transition-colors ${
                  statusFilter === st ? "bg-white text-slate-900 shadow-2xs" : "text-slate-500 hover:text-slate-900"
                }`}
              >
                {st}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Alerts List */}
      <div className="space-y-4">
        {alerts.length === 0 ? (
          <div className="p-12 text-center bg-white rounded-2xl border border-slate-200 text-slate-400">
            <CheckCircle2 className="w-8 h-8 text-emerald-500 mx-auto mb-2 opacity-80" />
            <p className="text-sm font-medium text-slate-700">All clear!</p>
            <p className="text-xs text-slate-400 mt-1">No alerts matching the selected filters.</p>
          </div>
        ) : (
          alerts.map((alert) => {
            const style = getSeverityStyle(alert.severity);
            const Icon = style.icon;

            return (
              <div
                key={alert.id}
                className={cn(
                  "p-5 rounded-2xl border flex flex-col sm:flex-row sm:items-center justify-between gap-4 transition-all shadow-xs",
                  style.bg
                )}
              >
                <div className="flex items-start gap-3.5">
                  <div className="p-2 rounded-xl bg-white shadow-2xs shrink-0 mt-0.5">
                    <Icon className={cn("w-5 h-5", style.iconColor)} />
                  </div>
                  <div>
                    <div className="flex items-center gap-2 font-mono">
                      <span
                        className={cn(
                          "text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded border",
                          style.badge
                        )}
                      >
                        {alert.severity}
                      </span>
                      <span className="text-[10px] font-semibold uppercase px-2 py-0.5 rounded bg-slate-100 text-slate-700 border border-slate-200">
                        {alert.type}
                      </span>
                      {alert.store_id && (
                        <span className="text-[10px] px-2 py-0.5 rounded bg-slate-100 text-slate-600 border">
                          Store #{alert.store_id}
                        </span>
                      )}
                      <span className="text-[11px] text-slate-500 font-medium">
                        {new Date(alert.created_at).toLocaleString()}
                      </span>
                    </div>
                    <p className="text-xs text-slate-800 mt-2 font-medium leading-relaxed">{alert.message}</p>
                  </div>
                </div>

                <div className="flex items-center gap-2 self-end sm:self-center shrink-0">
                  {alert.status === "new" && (
                    <button
                      onClick={() => handleUpdateStatus(alert.id, "acknowledged")}
                      className="text-xs px-3.5 py-1.5 rounded-xl bg-white border border-slate-200 hover:bg-slate-50 text-slate-700 font-semibold shadow-2xs transition-colors flex items-center gap-1.5"
                    >
                      <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
                      <span>Acknowledge</span>
                    </button>
                  )}
                  <button
                    onClick={() => handleUpdateStatus(alert.id, "dismissed")}
                    className="text-xs px-3 py-1.5 rounded-xl bg-slate-100 hover:bg-slate-200 text-slate-600 font-semibold transition-colors"
                  >
                    Dismiss
                  </button>
                </div>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
}
