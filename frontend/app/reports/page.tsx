"use client";

import React, { useState, useEffect } from "react";
import {
  FileBarChart2,
  Download,
  Sliders,
  TrendingUp,
  Percent,
  Calendar,
  Sparkles,
  DollarSign,
  Package,
  FileText,
  FileSpreadsheet,
  CheckCircle2,
  RefreshCw,
} from "lucide-react";
import ChartWrapper from "@/components/ChartWrapper";
import DataTable, { Column } from "@/components/DataTable";
import {
  ResponsiveContainer,
  ComposedChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  Legend,
} from "recharts";
import { api } from "@/lib/api";
import { ReportItem, SimulatePromoResponse } from "@/types";
import { useToast } from "@/context/ToastContext";

export default function ReportsPage() {
  const [activeTab, setActiveTab] = useState<"reports" | "simulator">("reports");
  const toast = useToast();

  // Tab 1: Reports State
  const [reports, setReports] = useState<ReportItem[]>([]);
  const [loadingReports, setLoadingReports] = useState<boolean>(true);
  const [isExporting, setIsExporting] = useState<boolean>(false);

  // Tab 2: What-If Simulator State
  const [discountPct, setDiscountPct] = useState<number>(20);
  const [durationDays, setDurationDays] = useState<number>(14);
  const [selectedProductId, setSelectedProductId] = useState<number>(1);
  const [simResult, setSimResult] = useState<SimulatePromoResponse | null>(null);
  const [simLoading, setSimLoading] = useState<boolean>(false);

  const fetchReports = async () => {
    setLoadingReports(true);
    try {
      const res = await api.reports.getReports(20, 0);
      setReports(res.items || []);
    } catch (err: any) {
      toast.error(err.message || "Failed to load reports.");
    } finally {
      setLoadingReports(false);
    }
  };

  const runSimulation = async () => {
    setSimLoading(true);
    try {
      const res = await api.simulation.simulatePromo({
        product_id: selectedProductId,
        discount_pct: discountPct,
        promo_duration_days: durationDays,
      });
      setSimResult(res);
    } catch (err: any) {
      toast.error(err.message || "Simulation failed.");
    } finally {
      setSimLoading(false);
    }
  };

  useEffect(() => {
    fetchReports();
  }, []);

  // Debounced simulation trigger on slider changes
  useEffect(() => {
    const timer = setTimeout(() => {
      runSimulation();
    }, 250);
    return () => clearTimeout(timer);
  }, [discountPct, durationDays, selectedProductId]);

  const handleExport = async (type: string, format: "csv" | "pdf") => {
    setIsExporting(true);
    try {
      const blob = await api.reports.exportReport(type, format);
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `demandiq_${type}_${Date.now()}.${format}`;
      document.body.appendChild(a);
      a.click();
      a.remove();
      window.URL.revokeObjectURL(url);
      toast.success(`Exported ${type.replace("_", " ")} as ${format.toUpperCase()}.`, "Report Downloaded");
    } catch (err: any) {
      toast.error(err.message || "Failed to export report.");
    } finally {
      setIsExporting(false);
    }
  };

  const reportColumns: Column<ReportItem>[] = [
    {
      header: "Report Title & Type",
      cell: (row) => (
        <div>
          <span className="font-bold text-slate-900 block">{row.title}</span>
          <span className="text-[11px] text-slate-500 font-mono">{row.report_type.replace("_", " ")}</span>
        </div>
      ),
    },
    {
      header: "Format",
      cell: (row) => (
        <span className="inline-flex items-center gap-1 text-[10px] font-bold font-mono px-2 py-0.5 rounded bg-slate-100 border text-slate-700 uppercase">
          {row.format === "pdf" ? <FileText className="w-3 h-3 text-rose-500" /> : <FileSpreadsheet className="w-3 h-3 text-emerald-600" />}
          {row.format}
        </span>
      ),
    },
    {
      header: "Generated Date",
      cell: (row) => (
        <span className="text-xs text-slate-600 font-mono">
          {new Date(row.created_at || Date.now()).toLocaleDateString()}
        </span>
      ),
    },
    {
      header: "Status",
      cell: (row) => (
        <span className="inline-flex items-center gap-1 text-[10px] font-bold font-mono px-2 py-0.5 rounded-full bg-emerald-50 text-emerald-700 border border-emerald-200">
          <CheckCircle2 className="w-3 h-3 text-emerald-600" />
          Ready
        </span>
      ),
    },
    {
      header: "Download Action",
      cell: (row) => (
        <div className="flex items-center gap-2">
          <button
            onClick={() => handleExport(row.report_type, "csv")}
            className="px-2.5 py-1 rounded-lg bg-white border border-slate-200 hover:bg-slate-50 text-slate-700 font-semibold text-xs transition-colors flex items-center gap-1"
          >
            <Download className="w-3 h-3 text-slate-500" />
            <span>CSV</span>
          </button>
          <button
            onClick={() => handleExport(row.report_type, "pdf")}
            className="px-2.5 py-1 rounded-lg bg-white border border-slate-200 hover:bg-slate-50 text-slate-700 font-semibold text-xs transition-colors flex items-center gap-1"
          >
            <Download className="w-3 h-3 text-slate-500" />
            <span>PDF</span>
          </button>
        </div>
      ),
    },
  ];

  return (
    <div className="space-y-8">
      {/* Header & Tabs */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">Analytics & What-If Simulator</h1>
          <p className="text-xs text-slate-500 mt-1">
            Historical forecast reports, accuracy audits, and interactive promotion impact simulations.
          </p>
        </div>

        {/* Tab Toggle */}
        <div className="flex items-center p-1 bg-white border border-slate-200 rounded-xl shadow-2xs">
          <button
            onClick={() => setActiveTab("reports")}
            className={`px-4 py-2 rounded-lg text-xs font-semibold flex items-center gap-2 transition-colors ${
              activeTab === "reports" ? "bg-slate-900 text-white" : "text-slate-600 hover:text-slate-900"
            }`}
          >
            <FileBarChart2 className="w-3.5 h-3.5" />
            <span>Executive Reports</span>
          </button>

          <button
            onClick={() => setActiveTab("simulator")}
            className={`px-4 py-2 rounded-lg text-xs font-semibold flex items-center gap-2 transition-colors ${
              activeTab === "simulator" ? "bg-teal-600 text-white" : "text-slate-600 hover:text-slate-900"
            }`}
          >
            <Sliders className="w-3.5 h-3.5" />
            <span>What-If Simulator</span>
          </button>
        </div>
      </div>

      {activeTab === "reports" ? (
        <div className="space-y-6">
          {/* Quick Export Cards */}
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <div className="p-4 rounded-2xl bg-white border border-slate-200 shadow-xs flex items-center justify-between">
              <div>
                <h4 className="font-bold text-xs text-slate-900">Demand Summary</h4>
                <p className="text-[11px] text-slate-500">Sales velocity and forecasts</p>
              </div>
              <button
                onClick={() => handleExport("demand_summary", "csv")}
                className="px-3 py-1.5 rounded-lg bg-slate-900 hover:bg-slate-800 text-white font-semibold text-xs flex items-center gap-1.5"
              >
                <Download className="w-3.5 h-3.5" />
                <span>Export</span>
              </button>
            </div>

            <div className="p-4 rounded-2xl bg-white border border-slate-200 shadow-xs flex items-center justify-between">
              <div>
                <h4 className="font-bold text-xs text-slate-900">Accuracy Benchmarks</h4>
                <p className="text-[11px] text-slate-500">MAPE and RMSE audit</p>
              </div>
              <button
                onClick={() => handleExport("accuracy_evaluation", "pdf")}
                className="px-3 py-1.5 rounded-lg bg-teal-600 hover:bg-teal-700 text-white font-semibold text-xs flex items-center gap-1.5"
              >
                <Download className="w-3.5 h-3.5" />
                <span>PDF Audit</span>
              </button>
            </div>

            <div className="p-4 rounded-2xl bg-white border border-slate-200 shadow-xs flex items-center justify-between">
              <div>
                <h4 className="font-bold text-xs text-slate-900">Inventory Health</h4>
                <p className="text-[11px] text-slate-500">Stockout and ROP risk report</p>
              </div>
              <button
                onClick={() => handleExport("inventory_health", "csv")}
                className="px-3 py-1.5 rounded-lg bg-slate-900 hover:bg-slate-800 text-white font-semibold text-xs flex items-center gap-1.5"
              >
                <Download className="w-3.5 h-3.5" />
                <span>Export</span>
              </button>
            </div>
          </div>

          {/* Reports Table */}
          <DataTable columns={reportColumns} data={reports} />
        </div>
      ) : (
        /* What-If Promotion Simulator */
        <div className="space-y-6">
          {/* Controls Bar */}
          <div className="p-6 rounded-2xl bg-white border border-slate-200 shadow-xs grid grid-cols-1 md:grid-cols-3 gap-6 text-xs">
            <div>
              <label className="block font-semibold text-slate-700 uppercase tracking-wider text-[11px] font-mono mb-2">
                Promotional Discount: <span className="text-teal-700 font-bold">{discountPct}% OFF</span>
              </label>
              <input
                type="range"
                min="0"
                max="50"
                step="5"
                value={discountPct}
                onChange={(e) => setDiscountPct(Number(e.target.value))}
                className="w-full accent-teal-600 cursor-pointer"
              />
              <div className="flex justify-between text-[10px] text-slate-400 font-mono mt-1">
                <span>0% (Baseline)</span>
                <span>25%</span>
                <span>50% (Max)</span>
              </div>
            </div>

            <div>
              <label className="block font-semibold text-slate-700 uppercase tracking-wider text-[11px] font-mono mb-2">
                Promotion Duration: <span className="text-teal-700 font-bold">{durationDays} Days</span>
              </label>
              <input
                type="range"
                min="3"
                max="60"
                step="1"
                value={durationDays}
                onChange={(e) => setDurationDays(Number(e.target.value))}
                className="w-full accent-teal-600 cursor-pointer"
              />
              <div className="flex justify-between text-[10px] text-slate-400 font-mono mt-1">
                <span>3 Days</span>
                <span>30 Days</span>
                <span>60 Days</span>
              </div>
            </div>

            <div>
              <label className="block font-semibold text-slate-700 uppercase tracking-wider text-[11px] font-mono mb-2">
                Simulated Product SKU
              </label>
              <select
                value={selectedProductId}
                onChange={(e) => setSelectedProductId(Number(e.target.value))}
                className="w-full px-3.5 py-2 bg-slate-50 border border-slate-200 rounded-xl text-slate-800 font-medium focus:outline-none focus:ring-2 focus:ring-teal-500/20"
              >
                <option value={1}>SKU-KEYBOARD: Ergonomic Keyboard ($89.99)</option>
                <option value={2}>SKU-MONITOR: 4K 27in Monitor ($299.99)</option>
              </select>
            </div>
          </div>

          {/* Simulation KPI Metrics */}
          {simResult && (
            <div className="grid grid-cols-1 sm:grid-cols-4 gap-4">
              <div className="p-4 rounded-2xl bg-white border border-slate-200 shadow-xs">
                <span className="text-slate-400 font-mono text-[10px] uppercase block">Price Elasticity</span>
                <span className="text-lg font-bold text-slate-900 font-mono">ε = {simResult.estimated_elasticity}</span>
                <span className="text-[11px] text-slate-500 block mt-0.5">High demand responsiveness</span>
              </div>

              <div className="p-4 rounded-2xl bg-white border border-slate-200 shadow-xs">
                <span className="text-slate-400 font-mono text-[10px] uppercase block">Total Unit Uplift</span>
                <span className="text-lg font-bold text-emerald-600 font-mono">
                  +{simResult.total_unit_uplift} units ({simResult.total_unit_uplift_pct}%)
                </span>
                <span className="text-[11px] text-slate-500 block mt-0.5">
                  {simResult.total_simulated_units} vs {simResult.total_baseline_units} baseline
                </span>
              </div>

              <div className="p-4 rounded-2xl bg-white border border-slate-200 shadow-xs">
                <span className="text-slate-400 font-mono text-[10px] uppercase block">Simulated Revenue</span>
                <span className="text-lg font-bold text-slate-900 font-mono">
                  ${simResult.total_simulated_revenue.toLocaleString()}
                </span>
                <span className="text-[11px] text-slate-500 block mt-0.5">
                  at {discountPct}% promotional pricing
                </span>
              </div>

              <div className="p-4 rounded-2xl bg-white border border-slate-200 shadow-xs">
                <span className="text-slate-400 font-mono text-[10px] uppercase block">Net Revenue Impact</span>
                <span
                  className={`text-lg font-bold font-mono ${
                    simResult.total_revenue_impact >= 0 ? "text-emerald-600" : "text-rose-600"
                  }`}
                >
                  {simResult.total_revenue_impact >= 0 ? `+$${simResult.total_revenue_impact.toLocaleString()}` : `-$${Math.abs(simResult.total_revenue_impact).toLocaleString()}`}
                </span>
                <span className="text-[11px] text-slate-500 block mt-0.5">Estimated margin balance</span>
              </div>
            </div>
          )}

          {/* Live Uplift Comparison Chart */}
          <ChartWrapper
            title="Simulated Promotional Uplift vs Baseline Demand"
            subtitle="Comparing daily baseline demand trajectory against price discounted demand curve"
            badge="Elasticity Simulation"
          >
            <ResponsiveContainer width="100%" height="100%">
              <ComposedChart data={simResult?.curve || []}>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#E2E8F0" />
                <XAxis dataKey="date" stroke="#94A3B8" fontSize={11} />
                <YAxis stroke="#94A3B8" fontSize={11} />
                <Tooltip
                  contentStyle={{
                    backgroundColor: "#0F172A",
                    borderColor: "#334155",
                    borderRadius: "8px",
                    color: "#F8FAFC",
                    fontSize: "12px",
                  }}
                />
                <Legend wrapperStyle={{ fontSize: "12px", paddingTop: "10px" }} />
                <Line
                  type="monotone"
                  dataKey="simulated_units"
                  stroke="#0D9488"
                  strokeWidth={3}
                  dot={{ r: 3, fill: "#0D9488" }}
                  name="Simulated Promo Demand (Units)"
                />
                <Line
                  type="monotone"
                  dataKey="baseline_units"
                  stroke="#64748B"
                  strokeWidth={2}
                  strokeDasharray="4 4"
                  dot={{ r: 2, fill: "#64748B" }}
                  name="Baseline Demand (Units)"
                />
              </ComposedChart>
            </ResponsiveContainer>
          </ChartWrapper>
        </div>
      )}
    </div>
  );
}
