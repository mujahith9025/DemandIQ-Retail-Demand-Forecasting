"use client";

import React, { useState, useEffect } from "react";
import {
  TrendingUp,
  AlertTriangle,
  DollarSign,
  Package,
  Boxes,
  Store as StoreIcon,
  RefreshCw,
  Sparkles,
} from "lucide-react";
import {
  AreaChart,
  Area,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  BarChart,
  Bar,
  ComposedChart,
} from "recharts";
import KPICard from "@/components/KPICard";
import ChartWrapper from "@/components/ChartWrapper";
import DataTable, { Column } from "@/components/DataTable";
import { api } from "@/lib/api";
import { DashboardKPIs } from "@/types";
import { useAuth } from "@/context/AuthContext";
import { useToast } from "@/context/ToastContext";

const mockTrendData = [
  { date: "Aug 01", historical_sales: 120, predicted_demand: 125, lower_bound: 110, upper_bound: 140 },
  { date: "Aug 05", historical_sales: 135, predicted_demand: 138, lower_bound: 120, upper_bound: 155 },
  { date: "Aug 10", historical_sales: 142, predicted_demand: 145, lower_bound: 128, upper_bound: 162 },
  { date: "Aug 15", historical_sales: 158, predicted_demand: 160, lower_bound: 140, upper_bound: 180 },
  { date: "Aug 20", historical_sales: 150, predicted_demand: 168, lower_bound: 148, upper_bound: 188 },
  { date: "Aug 25", historical_sales: 165, predicted_demand: 175, lower_bound: 152, upper_bound: 198 },
  { date: "Aug 30", historical_sales: null, predicted_demand: 182, lower_bound: 158, upper_bound: 206 },
  { date: "Sep 05", historical_sales: null, predicted_demand: 190, lower_bound: 165, upper_bound: 215 },
  { date: "Sep 10", historical_sales: null, predicted_demand: 195, lower_bound: 168, upper_bound: 222 },
];

const mockTopSkus = [
  { sku: "SKU-KEYBOARD", name: "Ergonomic Mechanical Keyboard", predicted_30d_units: 720, growth_pct: 12.4, category: "Electronics" },
  { sku: "SKU-MONITOR", name: "Ultra-HD 4K 27-inch Monitor", predicted_30d_units: 410, growth_pct: 8.6, category: "Displays" },
  { sku: "SKU-HEADSET", name: "Wireless Noise-Canceling Headset", predicted_30d_units: 350, growth_pct: -2.1, category: "Audio" },
  { sku: "SKU-DOCK-PRO", name: "Thunderbolt 4 Triple-Display Dock", predicted_30d_units: 280, growth_pct: 15.2, category: "Accessories" },
];

export default function DashboardPage() {
  const { user } = useAuth();
  const toast = useToast();
  const [kpis, setKpis] = useState<DashboardKPIs | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [selectedStore, setSelectedStore] = useState<number | null>(user?.assigned_store_id || null);

  const fetchKPIs = async () => {
    setLoading(true);
    try {
      const data = await api.dashboard.getKPIs(selectedStore);
      setKpis(data);
    } catch (e: any) {
      toast.error(e.message || "Failed to load dashboard KPIs.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchKPIs();
  }, [selectedStore]);

  const skuColumns: Column<any>[] = [
    { header: "SKU Code", accessorKey: "sku", className: "font-mono font-bold text-slate-900" },
    { header: "Product Name", accessorKey: "name", className: "font-medium text-slate-800" },
    { header: "Category", accessorKey: "category", className: "text-slate-500 font-mono text-xs" },
    {
      header: "30D Forecast (Units)",
      accessorKey: "predicted_30d_units",
      className: "text-right font-mono font-bold text-teal-700",
    },
    {
      header: "Projected Trend",
      cell: (row) => (
        <span
          className={`inline-flex items-center text-xs font-semibold px-2 py-0.5 rounded-full ${
            row.growth_pct >= 0
              ? "bg-emerald-50 text-emerald-700 border border-emerald-200"
              : "bg-rose-50 text-rose-700 border border-rose-200"
          }`}
        >
          {row.growth_pct >= 0 ? `+${row.growth_pct}%` : `${row.growth_pct}%`}
        </span>
      ),
    },
  ];

  const trendData = kpis?.trend_data && kpis.trend_data.length > 0 ? kpis.trend_data : mockTrendData;
  const topSkusData = kpis?.top_skus && kpis.top_skus.length > 0 ? kpis.top_skus : mockTopSkus;

  return (
    <div className="space-y-8 pb-12">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="p-1 rounded-md bg-teal-50 text-teal-700 font-mono text-2xs uppercase tracking-wider font-bold">
              Live Engine Telemetry
            </span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-slate-900 tracking-tight">Executive Dashboard</h1>
          <p className="text-xs sm:text-sm text-slate-500 mt-1">
            Enterprise retail demand forecasts, inventory health signals, and replenishment recommendations.
          </p>
        </div>

        <div className="flex items-center gap-3">
          {/* Store Selector (Disabled if Store Manager locked to assigned store) */}
          {!user?.assigned_store_id ? (
            <div className="flex items-center p-1 bg-white border border-slate-200 rounded-xl shadow-2xs">
              <button
                onClick={() => setSelectedStore(null)}
                className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-colors ${
                  selectedStore === null ? "bg-slate-900 text-white" : "text-slate-600 hover:text-slate-900"
                }`}
              >
                All Stores
              </button>
              <button
                onClick={() => setSelectedStore(1)}
                className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-colors ${
                  selectedStore === 1 ? "bg-slate-900 text-white" : "text-slate-600 hover:text-slate-900"
                }`}
              >
                Store 1 (Seattle)
              </button>
              <button
                onClick={() => setSelectedStore(2)}
                className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-colors ${
                  selectedStore === 2 ? "bg-slate-900 text-white" : "text-slate-600 hover:text-slate-900"
                }`}
              >
                Store 2 (NY)
              </button>
            </div>
          ) : (
            <div className="px-3 py-1.5 bg-amber-50 border border-amber-200 text-amber-900 text-xs font-mono font-semibold rounded-xl flex items-center gap-1.5">
              <StoreIcon className="w-3.5 h-3.5 text-amber-600" />
              <span>Assigned Store #{user.assigned_store_id}</span>
            </div>
          )}

          <button
            onClick={fetchKPIs}
            title="Refresh KPIs"
            className="p-2 bg-white border border-slate-200 hover:bg-slate-50 rounded-xl text-slate-600 transition-colors shadow-2xs"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? "animate-spin text-teal-600" : ""}`} />
          </button>
        </div>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
        <KPICard
          title="Projected 30D Revenue"
          value={loading ? "..." : `₹${(kpis?.projected_revenue_30d || 1482900).toLocaleString()}`}
          change={`+${kpis?.revenue_growth_pct || 8.4}%`}
          trend="up"
          icon={DollarSign}
          badgeColor="brand"
        />
        <KPICard
          title="Forecast Accuracy"
          value={loading ? "..." : `${kpis?.overall_accuracy_pct || 94.2}%`}
          change={`+${kpis?.accuracy_change_pct || 1.8}%`}
          trend="up"
          icon={TrendingUp}
          badgeColor="teal"
        />
        <KPICard
          title="Active Products"
          value={loading ? "..." : `${kpis?.total_active_products || 2} SKUs`}
          subtitle={`Across ${kpis?.total_stores || 2} active stores`}
          icon={Package}
          badgeColor="indigo"
        />
        <KPICard
          title="Stockout Risks"
          value={loading ? "..." : `${kpis?.stockout_risk_count || 1} SKUs`}
          subtitle={`${kpis?.urgent_reorder_count || 1} urgent reorders`}
          badgeColor="rose"
          icon={AlertTriangle}
        />
      </div>

      {/* Charts Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2">
          <ChartWrapper
            title="Enterprise Demand vs Historical Sales"
            subtitle="Actual historical units vs 95% confidence interval forecast band"
            badge="Ensemble AI"
          >
            <ResponsiveContainer width="100%" height="100%">
              <ComposedChart data={trendData}>
                <defs>
                  <linearGradient id="colorBand" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#14B8A6" stopOpacity={0.25} />
                    <stop offset="95%" stopColor="#14B8A6" stopOpacity={0.05} />
                  </linearGradient>
                </defs>
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
                <Area
                  type="monotone"
                  dataKey="upper_bound"
                  stroke="transparent"
                  fill="url(#colorBand)"
                  name="Upper 95% Band"
                />
                <Area
                  type="monotone"
                  dataKey="lower_bound"
                  stroke="transparent"
                  fill="#ffffff"
                  name="Lower 95% Band"
                />
                <Line
                  type="monotone"
                  dataKey="predicted_demand"
                  stroke="#14B8A6"
                  strokeWidth={2.5}
                  dot={{ r: 3, fill: "#14B8A6" }}
                  name="Predicted Demand"
                />
                <Line
                  type="monotone"
                  dataKey="historical_sales"
                  stroke="#1E3A5F"
                  strokeWidth={2}
                  dot={{ r: 3, fill: "#1E3A5F" }}
                  name="Historical Sales"
                />
              </ComposedChart>
            </ResponsiveContainer>
          </ChartWrapper>
        </div>

        <div>
          <ChartWrapper title="Forecast Accuracy by Category" subtitle="Recent ensemble validation">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart
                data={[
                  { category: "Electronics", accuracy: 96.2 },
                  { category: "Displays", accuracy: 94.8 },
                  { category: "Audio", accuracy: 91.5 },
                  { category: "Peripherals", accuracy: 95.0 },
                ]}
                layout="vertical"
              >
                <CartesianGrid strokeDasharray="3 3" horizontal={false} stroke="#E2E8F0" />
                <XAxis type="number" domain={[80, 100]} stroke="#94A3B8" fontSize={11} />
                <YAxis dataKey="category" type="category" stroke="#94A3B8" fontSize={11} width={80} />
                <Tooltip />
                <Bar dataKey="accuracy" fill="#0D9488" radius={[0, 6, 6, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </ChartWrapper>
        </div>
      </div>

      {/* Top SKUs Table */}
      <div>
        <div className="flex items-center justify-between mb-4">
          <div>
            <h3 className="font-bold text-slate-900 text-lg">Top Projected Demand SKUs</h3>
            <p className="text-xs text-slate-500">Highest velocity products over the next 30-day forecast horizon</p>
          </div>
          <span className="text-xs text-slate-500 font-mono bg-white px-3 py-1 rounded-lg border border-slate-200">
            Next 30-Day Window
          </span>
        </div>
        <DataTable columns={skuColumns} data={topSkusData} />
      </div>
    </div>
  );
}
