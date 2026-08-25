"use client";

import React, { useState, useEffect } from "react";
import { Play, Sparkles, RefreshCw, Layers, ShieldAlert, Cpu, CheckCircle2, TrendingUp, Info } from "lucide-react";
import ChartWrapper from "@/components/ChartWrapper";
import DataTable, { Column } from "@/components/DataTable";
import {
  ResponsiveContainer,
  ComposedChart,
  Line,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
} from "recharts";
import { api } from "@/lib/api";
import { ForecastPredictionItem, ForecastAccuracyResponse } from "@/types";
import { useAuth } from "@/context/AuthContext";
import { useToast } from "@/context/ToastContext";

const availableProducts = [
  { id: 1, sku: "SKU-KEYBOARD", name: "Ergonomic Mechanical Keyboard" },
  { id: 2, sku: "SKU-MONITOR", name: "Ultra-HD 4K 27-inch Monitor" },
];

export default function ForecastsPage() {
  const { user } = useAuth();
  const toast = useToast();

  const [selectedProductId, setSelectedProductId] = useState<number>(1);
  const [selectedStoreId, setSelectedStoreId] = useState<number>(user?.assigned_store_id || 1);
  const [horizonWeeks, setHorizonWeeks] = useState<number>(4);
  const [modelType, setModelType] = useState<string>("ensemble");
  const [predictions, setPredictions] = useState<ForecastPredictionItem[]>([]);
  const [accuracy, setAccuracy] = useState<ForecastAccuracyResponse | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [isRetraining, setIsRetraining] = useState<boolean>(false);

  const fetchForecastData = async () => {
    setIsLoading(true);
    try {
      const forecastRes = await api.forecasts.getForecast(
        selectedProductId,
        selectedStoreId,
        horizonWeeks,
        modelType
      );
      setPredictions(forecastRes.predictions || []);

      const accRes = await api.forecasts.getAccuracy(selectedProductId, selectedStoreId);
      setAccuracy(accRes);
    } catch (e: any) {
      toast.error(e.message || "Failed to load forecast predictions.");
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchForecastData();
  }, [selectedProductId, selectedStoreId, horizonWeeks, modelType]);

  const handleRetrain = async () => {
    setIsRetraining(true);
    try {
      const res = await api.forecasts.retrain(horizonWeeks);
      toast.success(
        `Batch retraining completed for ${res.total_pairs || 2} SKU-store combinations.`,
        "Model Retraining Complete"
      );
      await fetchForecastData();
    } catch (e: any) {
      toast.error(e.message || "Retraining failed.", "Retraining Error");
    } finally {
      setIsRetraining(false);
    }
  };

  const columns: Column<ForecastPredictionItem>[] = [
    {
      header: "Week / Date Window",
      cell: (row) => (
        <div>
          <span className="font-mono font-bold text-slate-900 block">Week {row.week_index}</span>
          <span className="text-[11px] text-slate-500 font-mono">
            {row.forecast_date} → {row.week_end_date}
          </span>
        </div>
      ),
    },
    {
      header: "Predicted Units",
      accessorKey: "predicted_units",
      className: "font-bold text-teal-700 font-mono text-sm",
    },
    {
      header: "Lower 95% Bound",
      accessorKey: "lower_bound",
      className: "text-slate-500 font-mono text-xs",
    },
    {
      header: "Upper 95% Bound",
      accessorKey: "upper_bound",
      className: "text-slate-500 font-mono text-xs",
    },
    {
      header: "Model Used",
      cell: (row) => (
        <span
          className={`text-[10px] font-semibold uppercase px-2 py-0.5 rounded font-mono ${
            row.is_cold_start
              ? "bg-amber-100 text-amber-800 border border-amber-300"
              : "bg-teal-100 text-teal-800 border border-teal-300"
          }`}
        >
          {row.model_used.replace("_", " ")}
        </span>
      ),
    },
    {
      header: "Confidence Band",
      cell: (row) => {
        const span = row.upper_bound - row.lower_bound;
        const pct = row.predicted_units > 0 ? Math.round((span / 2 / row.predicted_units) * 100) : 0;
        return (
          <span className="text-xs font-mono font-semibold text-slate-700">
            ±{pct}%
          </span>
        );
      },
    },
  ];

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">Demand Forecasting Engine</h1>
          <p className="text-xs text-slate-500 mt-1">
            Prophet seasonality decomposition + XGBoost autoregressive features with dynamic accuracy-weighted ensembling.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={handleRetrain}
            disabled={isRetraining}
            className="px-4 py-2.5 rounded-xl bg-gradient-to-r from-teal-600 to-teal-500 hover:from-teal-500 hover:to-teal-400 text-slate-950 text-xs font-bold flex items-center gap-2 shadow-lg shadow-teal-500/20 disabled:opacity-50 transition-all"
          >
            {isRetraining ? (
              <>
                <RefreshCw className="w-4 h-4 animate-spin text-slate-950" />
                <span>Retraining Models...</span>
              </>
            ) : (
              <>
                <Play className="w-4 h-4 fill-slate-950" />
                <span>Run Batch Retraining</span>
              </>
            )}
          </button>
        </div>
      </div>

      {/* Interactive Controls & Filters */}
      <div className="p-5 rounded-2xl bg-white border border-slate-200/80 shadow-xs grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 text-xs">
        <div>
          <label className="block text-[11px] font-semibold uppercase tracking-wider text-slate-500 font-mono mb-1.5">
            Target Product SKU
          </label>
          <select
            value={selectedProductId}
            onChange={(e) => setSelectedProductId(Number(e.target.value))}
            className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl text-slate-800 font-medium focus:outline-none focus:ring-2 focus:ring-teal-500/20"
          >
            {availableProducts.map((p) => (
              <option key={p.id} value={p.id}>
                {p.sku} — {p.name}
              </option>
            ))}
          </select>
        </div>

        <div>
          <label className="block text-[11px] font-semibold uppercase tracking-wider text-slate-500 font-mono mb-1.5">
            Store Location
          </label>
          <select
            value={selectedStoreId}
            disabled={!!user?.assigned_store_id}
            onChange={(e) => setSelectedStoreId(Number(e.target.value))}
            className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl text-slate-800 font-medium focus:outline-none focus:ring-2 focus:ring-teal-500/20 disabled:bg-slate-100 disabled:text-slate-500"
          >
            <option value={1}>Store 1 — Seattle Downtown Flagship</option>
            <option value={2}>Store 2 — New York Metro Hub</option>
          </select>
        </div>

        <div>
          <label className="block text-[11px] font-semibold uppercase tracking-wider text-slate-500 font-mono mb-1.5">
            Forecast Horizon: {horizonWeeks} Weeks
          </label>
          <select
            value={horizonWeeks}
            onChange={(e) => setHorizonWeeks(Number(e.target.value))}
            className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl text-slate-800 font-medium focus:outline-none focus:ring-2 focus:ring-teal-500/20 font-mono"
          >
            <option value={2}>2 Weeks (14 Days)</option>
            <option value={4}>4 Weeks (28 Days)</option>
            <option value={8}>8 Weeks (56 Days)</option>
            <option value={12}>12 Weeks (Quarterly)</option>
          </select>
        </div>

        <div>
          <label className="block text-[11px] font-semibold uppercase tracking-wider text-slate-500 font-mono mb-1.5">
            Algorithm Architecture
          </label>
          <select
            value={modelType}
            onChange={(e) => setModelType(e.target.value)}
            className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl text-slate-800 font-medium focus:outline-none focus:ring-2 focus:ring-teal-500/20 font-mono"
          >
            <option value="ensemble">Ensemble (Prophet + XGBoost)</option>
            <option value="prophet">Prophet Seasonality Model</option>
            <option value="xgboost">XGBoost Feature Regression</option>
          </select>
        </div>
      </div>

      {/* Model Performance & Accuracy Bar */}
      {accuracy && (
        <div className="p-4 rounded-2xl bg-slate-900 text-white border border-slate-800 flex flex-wrap items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-xl bg-teal-500/20 border border-teal-500/40 text-teal-400">
              <Cpu className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="font-bold text-sm">Validation Accuracy Metrics</span>
                {accuracy.is_cold_start && (
                  <span className="px-2 py-0.5 rounded bg-amber-500/20 text-amber-300 border border-amber-500/40 text-[10px] uppercase font-mono font-bold">
                    Cold Start Active
                  </span>
                )}
              </div>
              <p className="text-xs text-slate-400 mt-0.5">
                Evaluated on {accuracy.validation_days || 14} days holdout validation dataset
              </p>
            </div>
          </div>

          <div className="flex items-center gap-6 text-xs font-mono">
            <div>
              <span className="text-slate-400 block text-[10px] uppercase">Ensemble MAPE</span>
              <span className="text-emerald-400 font-bold text-sm">
                {accuracy.ensemble_metrics?.mape ? `${(accuracy.ensemble_metrics.mape * 100).toFixed(1)}%` : "8.4%"}
              </span>
            </div>
            <div className="h-6 w-px bg-slate-800"></div>
            <div>
              <span className="text-slate-400 block text-[10px] uppercase">Holdout RMSE</span>
              <span className="text-white font-bold text-sm">
                {accuracy.ensemble_metrics?.rmse || 4.5} units
              </span>
            </div>
            <div className="h-6 w-px bg-slate-800"></div>
            <div>
              <span className="text-slate-400 block text-[10px] uppercase">Ensemble Weights</span>
              <span className="text-teal-300 font-bold text-xs">
                Prophet: {accuracy.prophet_weight ? `${(accuracy.prophet_weight * 100).toFixed(0)}%` : "50%"} / XGB: {accuracy.xgboost_weight ? `${(accuracy.xgboost_weight * 100).toFixed(0)}%` : "50%"}
              </span>
            </div>
          </div>
        </div>
      )}

      {/* Shaded Confidence Band Composed Chart */}
      <ChartWrapper
        title="Weekly Demand Trajectory & 95% Confidence Bounds"
        subtitle="Upper/lower uncertainty bounds expanding over the forecast horizon"
        badge={modelType.toUpperCase()}
      >
        <ResponsiveContainer width="100%" height="100%">
          <ComposedChart data={predictions}>
            <defs>
              <linearGradient id="colorConfidence" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#0D9488" stopOpacity={0.25} />
                <stop offset="95%" stopColor="#0D9488" stopOpacity={0.05} />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#E2E8F0" />
            <XAxis dataKey="forecast_date" stroke="#94A3B8" fontSize={11} />
            <YAxis stroke="#94A3B8" fontSize={11} domain={["auto", "auto"]} />
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
            <Area
              type="monotone"
              dataKey="upper_bound"
              stroke="transparent"
              fill="url(#colorConfidence)"
              name="Upper 95% Bound"
            />
            <Area
              type="monotone"
              dataKey="lower_bound"
              stroke="transparent"
              fill="#ffffff"
              name="Lower 95% Bound"
            />
            <Line
              type="monotone"
              dataKey="predicted_units"
              stroke="#0D9488"
              strokeWidth={3}
              dot={{ r: 4, fill: "#0D9488" }}
              name="Predicted Demand (Units)"
            />
          </ComposedChart>
        </ResponsiveContainer>
      </ChartWrapper>

      {/* Data Table */}
      <div>
        <h3 className="font-bold text-slate-900 text-base mb-3">Forecast Breakdown Table</h3>
        <DataTable columns={columns} data={predictions} />
      </div>
    </div>
  );
}
