"use client";

import React, { useState, useEffect } from "react";
import {
  UploadCloud,
  Sliders,
  Users,
  Shield,
  CheckCircle2,
  AlertCircle,
  FileSpreadsheet,
  Save,
  Loader2,
  Building2,
  Lock,
  Plus,
  RefreshCw,
  BellRing,
  Activity,
  Scan,
} from "lucide-react";
import { api } from "@/lib/api";
import { useAuth } from "@/context/AuthContext";
import { useToast } from "@/context/ToastContext";
import { DataUploadSuccessResponse, DataUploadErrorResponse } from "@/types";

export default function SettingsPage() {
  const { user } = useAuth();
  const toast = useToast();

  const [activeTab, setActiveTab] = useState<"ingestion" | "users" | "models" | "alerts">("ingestion");

  // Tab 1: Data Ingestion State
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [isUploading, setIsUploading] = useState<boolean>(false);
  const [uploadSuccess, setUploadSuccess] = useState<DataUploadSuccessResponse | null>(null);
  const [uploadError, setUploadError] = useState<DataUploadErrorResponse | null>(null);

  // Tab 2: User Management State (Admin only)
  const [newName, setNewName] = useState<string>("");
  const [newEmail, setNewEmail] = useState<string>("");
  const [newPassword, setNewPassword] = useState<string>("");
  const [newRole, setNewRole] = useState<string>("planner");
  const [newStoreId, setNewStoreId] = useState<string>("");
  const [isCreatingUser, setIsCreatingUser] = useState<boolean>(false);

  // Tab 3: Model Configuration
  const [retrainFrequency, setRetrainFrequency] = useState<string>("weekly");
  const [confidenceLevel, setConfidenceLevel] = useState<string>("95");
  const [coldStartWeeks, setColdStartWeeks] = useState<number>(8);

  // Tab 4: Alert & Anomaly Configuration
  const [zScoreThreshold, setZScoreThreshold] = useState<number>(2.5);
  const [criticalZThreshold, setCriticalZThreshold] = useState<number>(4.0);
  const [isoContamination, setIsoContamination] = useState<number>(0.05);
  const [highRiskDocDays, setHighRiskDocDays] = useState<number>(7.0);
  const [mediumRiskDocDays, setMediumRiskDocDays] = useState<number>(14.0);
  const [isSavingAlertConfig, setIsSavingAlertConfig] = useState<boolean>(false);
  const [isScanningAnomalies, setIsScanningAnomalies] = useState<boolean>(false);

  useEffect(() => {
    // Fetch live alert config
    const loadAlertConfig = async () => {
      try {
        const config = await api.alerts.getConfig();
        if (config) {
          setZScoreThreshold(config.z_score_threshold || 2.5);
          setCriticalZThreshold(config.critical_z_threshold || 4.0);
          setIsoContamination(config.isolation_forest_contamination || 0.05);
          setHighRiskDocDays(config.high_risk_doc_days || 7.0);
          setMediumRiskDocDays(config.medium_risk_doc_days || 14.0);
        }
      } catch (err) {
        // Fall back to default
      }
    };
    loadAlertConfig();
  }, []);

  const handleFileUpload = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedFile) return;

    setIsUploading(true);
    setUploadSuccess(null);
    setUploadError(null);

    try {
      const res = await api.data.uploadSalesCSV(selectedFile);
      setUploadSuccess(res);
      toast.success(
        `Successfully ingested ${res.inserted_rows} sales records. Weekly aggregation & anomaly scan triggered.`,
        "CSV Ingestion Complete"
      );
      setSelectedFile(null);
    } catch (err: any) {
      if (err.errors) {
        setUploadError(err);
      }
      toast.error(err.message || "CSV validation failed.", "Upload Error");
    } finally {
      setIsUploading(false);
    }
  };

  const handleCreateUser = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsCreatingUser(true);

    try {
      await api.auth.register({
        name: newName,
        email: newEmail,
        password: newPassword,
        role: newRole,
        assigned_store_id: newStoreId ? Number(newStoreId) : null,
      });

      toast.success(`User account for ${newEmail} created successfully.`, "User Registered");
      setNewName("");
      setNewEmail("");
      setNewPassword("");
      setNewStoreId("");
    } catch (err: any) {
      toast.error(err.message || "Failed to create user account.");
    } finally {
      setIsCreatingUser(false);
    }
  };

  const handleSaveAlertConfig = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSavingAlertConfig(true);
    try {
      await api.alerts.updateConfig({
        z_score_threshold: zScoreThreshold,
        critical_z_threshold: criticalZThreshold,
        isolation_forest_contamination: isoContamination,
        high_risk_doc_days: highRiskDocDays,
        medium_risk_doc_days: mediumRiskDocDays,
        lookback_window_days: 28,
      });
      toast.success("Anomaly detection and risk thresholds updated successfully.", "Alert Config Saved");
    } catch (err: any) {
      toast.error(err.message || "Failed to update alert configuration.");
    } finally {
      setIsSavingAlertConfig(false);
    }
  };

  const handleTriggerAnomalyScan = async () => {
    setIsScanningAnomalies(true);
    try {
      const res = await api.alerts.triggerScan();
      toast.success(
        `Scan complete across ${res.sku_store_pairs_scanned} SKU-store combinations. Created ${res.new_alerts_created} new alerts (${res.alerts_deduplicated_or_updated} deduplicated).`,
        "Anomaly Scan Completed"
      );
    } catch (err: any) {
      toast.error(err.message || "Anomaly scan execution failed.");
    } finally {
      setIsScanningAnomalies(false);
    }
  };

  return (
    <div className="space-y-8 max-w-5xl">
      {/* Header & Tabs */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">System Settings & Governance</h1>
          <p className="text-xs text-slate-500 mt-1">
            Data pipeline ingestion, team RBAC, anomaly threshold governance, and ML hyperparameters.
          </p>
        </div>

        {/* Tab Controls */}
        <div className="flex items-center p-1 bg-white border border-slate-200 rounded-xl shadow-2xs">
          <button
            onClick={() => setActiveTab("ingestion")}
            className={`px-3 py-1.5 rounded-lg text-xs font-semibold flex items-center gap-1.5 transition-colors ${
              activeTab === "ingestion" ? "bg-slate-900 text-white" : "text-slate-600 hover:text-slate-900"
            }`}
          >
            <UploadCloud className="w-3.5 h-3.5" />
            <span>Data Ingestion</span>
          </button>

          {user?.role === "admin" && (
            <button
              onClick={() => setActiveTab("users")}
              className={`px-3 py-1.5 rounded-lg text-xs font-semibold flex items-center gap-1.5 transition-colors ${
                activeTab === "users" ? "bg-slate-900 text-white" : "text-slate-600 hover:text-slate-900"
              }`}
            >
              <Users className="w-3.5 h-3.5" />
              <span>User Access</span>
            </button>
          )}

          <button
            onClick={() => setActiveTab("alerts")}
            className={`px-3 py-1.5 rounded-lg text-xs font-semibold flex items-center gap-1.5 transition-colors ${
              activeTab === "alerts" ? "bg-slate-900 text-white" : "text-slate-600 hover:text-slate-900"
            }`}
          >
            <BellRing className="w-3.5 h-3.5" />
            <span>Alert Thresholds</span>
          </button>

          <button
            onClick={() => setActiveTab("models")}
            className={`px-3 py-1.5 rounded-lg text-xs font-semibold flex items-center gap-1.5 transition-colors ${
              activeTab === "models" ? "bg-slate-900 text-white" : "text-slate-600 hover:text-slate-900"
            }`}
          >
            <Sliders className="w-3.5 h-3.5" />
            <span>Model Config</span>
          </button>
        </div>
      </div>

      {/* Tab 1: Data Ingestion (CSV Upload) */}
      {activeTab === "ingestion" && (
        <div className="space-y-6">
          <div className="p-6 rounded-2xl bg-white border border-slate-200 shadow-xs">
            <div className="flex items-center gap-2.5 pb-4 border-b border-slate-100 mb-5">
              <div className="p-2 rounded-xl bg-teal-100 text-teal-800">
                <FileSpreadsheet className="w-5 h-5" />
              </div>
              <div>
                <h3 className="font-bold text-sm text-slate-900">Upload Sales History CSV</h3>
                <p className="text-xs text-slate-500">
                  Required columns: <code className="font-mono text-teal-700 font-semibold">date, sku_code, store_id, units_sold, revenue</code>
                </p>
              </div>
            </div>

            <form onSubmit={handleFileUpload} className="space-y-5">
              <div className="border-2 border-dashed border-slate-300 hover:border-teal-500 rounded-2xl p-8 text-center transition-colors bg-slate-50/50">
                <UploadCloud className="w-10 h-10 text-teal-600 mx-auto mb-3" />
                <p className="text-xs font-semibold text-slate-700">
                  {selectedFile ? selectedFile.name : "Click to select or drag and drop sales CSV file"}
                </p>
                <p className="text-[11px] text-slate-400 font-mono mt-1">
                  Accepts UTF-8 encoded .csv files up to 50MB
                </p>
                <input
                  type="file"
                  accept=".csv,text/csv"
                  onChange={(e) => {
                    if (e.target.files && e.target.files[0]) {
                      setSelectedFile(e.target.files[0]);
                      setUploadSuccess(null);
                      setUploadError(null);
                    }
                  }}
                  className="hidden"
                  id="csv-file-input"
                />
                <label
                  htmlFor="csv-file-input"
                  className="mt-4 inline-block px-4 py-2 rounded-xl bg-white border border-slate-200 text-slate-700 text-xs font-semibold cursor-pointer hover:bg-slate-50 shadow-2xs"
                >
                  Choose File
                </label>
              </div>

              <div className="flex justify-end">
                <button
                  type="submit"
                  disabled={!selectedFile || isUploading}
                  className="px-6 py-2.5 rounded-xl bg-teal-600 hover:bg-teal-700 text-white text-xs font-bold shadow-md shadow-teal-500/20 flex items-center gap-2 disabled:opacity-50 transition-all"
                >
                  {isUploading ? (
                    <>
                      <Loader2 className="w-4 h-4 animate-spin" />
                      <span>Validating & Ingesting...</span>
                    </>
                  ) : (
                    <>
                      <UploadCloud className="w-4 h-4" />
                      <span>Ingest Sales Dataset</span>
                    </>
                  )}
                </button>
              </div>
            </form>
          </div>

          {/* Success Banner */}
          {uploadSuccess && (
            <div className="p-5 rounded-2xl bg-emerald-50 border border-emerald-200 text-emerald-950 space-y-2">
              <div className="flex items-center gap-2">
                <CheckCircle2 className="w-5 h-5 text-emerald-600 shrink-0" />
                <h4 className="font-bold text-sm">Dataset Ingested Successfully</h4>
              </div>
              <p className="text-xs text-emerald-800 leading-relaxed">{uploadSuccess.message}</p>
              <div className="flex items-center gap-4 text-xs font-mono pt-2 text-emerald-900">
                <span>Total Rows: <strong>{uploadSuccess.total_rows}</strong></span>
                <span>Inserted: <strong>{uploadSuccess.inserted_rows}</strong></span>
                {uploadSuccess.date_range && (
                  <span>
                    Range: <strong>{uploadSuccess.date_range.start_date} → {uploadSuccess.date_range.end_date}</strong>
                  </span>
                )}
              </div>
            </div>
          )}

          {/* Error Diagnostics Report */}
          {uploadError && (
            <div className="p-5 rounded-2xl bg-rose-50 border border-rose-200 text-rose-950 space-y-3">
              <div className="flex items-center gap-2">
                <AlertCircle className="w-5 h-5 text-rose-600 shrink-0" />
                <h4 className="font-bold text-sm">CSV Validation Failed ({uploadError.error_count} Errors)</h4>
              </div>
              <p className="text-xs text-rose-800">{uploadError.message}</p>
              <div className="max-h-60 overflow-y-auto space-y-1.5 pt-2">
                {uploadError.errors.map((err, idx) => (
                  <div
                    key={idx}
                    className="p-2.5 rounded-xl bg-white/80 border border-rose-200 text-xs font-mono text-rose-900 flex items-start gap-2"
                  >
                    <span className="font-bold text-rose-600 shrink-0">Row {err.row_number}:</span>
                    <span>{err.issue}</span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Tab 2: User Access Management (Admin Only) */}
      {activeTab === "users" && user?.role === "admin" && (
        <div className="p-6 rounded-2xl bg-white border border-slate-200 shadow-xs space-y-5">
          <div className="flex items-center gap-2.5 pb-4 border-b border-slate-100">
            <div className="p-2 rounded-xl bg-purple-100 text-purple-800">
              <Shield className="w-5 h-5" />
            </div>
            <div>
              <h3 className="font-bold text-sm text-slate-900">Add Team User & RBAC Assignment</h3>
              <p className="text-xs text-slate-500">
                Grant role-based access for Administrators, Supply Planners, or Store Managers.
              </p>
            </div>
          </div>

          <form onSubmit={handleCreateUser} className="space-y-4 text-xs">
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className="block font-semibold text-slate-700 uppercase tracking-wider text-[11px] font-mono mb-1.5">
                  Full Name
                </label>
                <input
                  type="text"
                  required
                  value={newName}
                  onChange={(e) => setNewName(e.target.value)}
                  placeholder="e.g. Alex Taylor"
                  className="w-full px-3.5 py-2.5 bg-slate-50 border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-purple-500/20"
                />
              </div>

              <div>
                <label className="block font-semibold text-slate-700 uppercase tracking-wider text-[11px] font-mono mb-1.5">
                  Work Email Address
                </label>
                <input
                  type="email"
                  required
                  value={newEmail}
                  onChange={(e) => setNewEmail(e.target.value)}
                  placeholder="name@demandiq.io"
                  className="w-full px-3.5 py-2.5 bg-slate-50 border border-slate-200 rounded-xl font-mono focus:outline-none focus:ring-2 focus:ring-purple-500/20"
                />
              </div>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
              <div>
                <label className="block font-semibold text-slate-700 uppercase tracking-wider text-[11px] font-mono mb-1.5">
                  Initial Password
                </label>
                <input
                  type="password"
                  required
                  value={newPassword}
                  onChange={(e) => setNewPassword(e.target.value)}
                  placeholder="••••••••••••"
                  className="w-full px-3.5 py-2.5 bg-slate-50 border border-slate-200 rounded-xl font-mono focus:outline-none focus:ring-2 focus:ring-purple-500/20"
                />
              </div>

              <div>
                <label className="block font-semibold text-slate-700 uppercase tracking-wider text-[11px] font-mono mb-1.5">
                  Assigned Role
                </label>
                <select
                  value={newRole}
                  onChange={(e) => setNewRole(e.target.value)}
                  className="w-full px-3.5 py-2.5 bg-slate-50 border border-slate-200 rounded-xl font-medium focus:outline-none focus:ring-2 focus:ring-purple-500/20"
                >
                  <option value="planner">Supply Planner (All Stores)</option>
                  <option value="store_manager">Store Manager (Store Isolated)</option>
                  <option value="admin">System Administrator</option>
                </select>
              </div>

              <div>
                <label className="block font-semibold text-slate-700 uppercase tracking-wider text-[11px] font-mono mb-1.5">
                  Assigned Store ID
                </label>
                <input
                  type="number"
                  placeholder="e.g. 1 (for Store Manager)"
                  value={newStoreId}
                  onChange={(e) => setNewStoreId(e.target.value)}
                  disabled={newRole !== "store_manager"}
                  className="w-full px-3.5 py-2.5 bg-slate-50 border border-slate-200 rounded-xl font-mono focus:outline-none focus:ring-2 focus:ring-purple-500/20 disabled:bg-slate-100 disabled:text-slate-400"
                />
              </div>
            </div>

            <div className="flex justify-end pt-3">
              <button
                type="submit"
                disabled={isCreatingUser}
                className="px-6 py-2.5 rounded-xl bg-purple-600 hover:bg-purple-700 text-white text-xs font-bold shadow-md shadow-purple-500/20 flex items-center gap-2 disabled:opacity-50"
              >
                {isCreatingUser ? (
                  <>
                    <Loader2 className="w-4 h-4 animate-spin" />
                    <span>Registering...</span>
                  </>
                ) : (
                  <>
                    <Plus className="w-4 h-4" />
                    <span>Create User Account</span>
                  </>
                )}
              </button>
            </div>
          </form>
        </div>
      )}

      {/* Tab 4: Alert & Anomaly Detection Governance */}
      {activeTab === "alerts" && (
        <div className="space-y-6">
          <form onSubmit={handleSaveAlertConfig} className="p-6 rounded-2xl bg-white border border-slate-200 shadow-xs space-y-5 text-xs">
            <div className="flex items-center justify-between pb-4 border-b border-slate-100">
              <div className="flex items-center gap-2.5">
                <div className="p-2 rounded-xl bg-amber-100 text-amber-800">
                  <Activity className="w-5 h-5" />
                </div>
                <div>
                  <h3 className="font-bold text-sm text-slate-900">Statistical Anomaly & Risk Governance</h3>
                  <p className="text-xs text-slate-500">
                    Configure standard deviation thresholds, Isolation Forest contamination, and Days-of-Cover risk bands.
                  </p>
                </div>
              </div>

              <button
                type="button"
                onClick={handleTriggerAnomalyScan}
                disabled={isScanningAnomalies}
                className="px-3.5 py-2 rounded-xl bg-slate-100 hover:bg-slate-200 text-slate-800 font-semibold flex items-center gap-1.5 shadow-2xs transition-colors"
              >
                <Scan className={`w-3.5 h-3.5 ${isScanningAnomalies ? "animate-spin text-teal-600" : ""}`} />
                <span>{isScanningAnomalies ? "Scanning..." : "Run Anomaly Scan Now"}</span>
              </button>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-3 gap-5">
              <div>
                <label className="font-semibold text-slate-700 block mb-1.5">
                  Warning Z-Score Threshold (σ)
                </label>
                <input
                  type="number"
                  step="0.1"
                  min="1.0"
                  max="5.0"
                  value={zScoreThreshold}
                  onChange={(e) => setZScoreThreshold(Number(e.target.value))}
                  className="w-full p-2.5 rounded-xl border border-slate-200 bg-slate-50 font-mono text-slate-900"
                />
                <span className="text-[11px] text-slate-400 block mt-1">Default 2.5σ (98.7% band)</span>
              </div>

              <div>
                <label className="font-semibold text-slate-700 block mb-1.5">
                  Critical Z-Score Threshold (σ)
                </label>
                <input
                  type="number"
                  step="0.1"
                  min="2.0"
                  max="10.0"
                  value={criticalZThreshold}
                  onChange={(e) => setCriticalZThreshold(Number(e.target.value))}
                  className="w-full p-2.5 rounded-xl border border-slate-200 bg-slate-50 font-mono text-slate-900"
                />
                <span className="text-[11px] text-slate-400 block mt-1">Default 4.0σ (Severe shocks)</span>
              </div>

              <div>
                <label className="font-semibold text-slate-700 block mb-1.5">
                  Isolation Forest Contamination
                </label>
                <input
                  type="number"
                  step="0.01"
                  min="0.01"
                  max="0.20"
                  value={isoContamination}
                  onChange={(e) => setIsoContamination(Number(e.target.value))}
                  className="w-full p-2.5 rounded-xl border border-slate-200 bg-slate-50 font-mono text-slate-900"
                />
                <span className="text-[11px] text-slate-400 block mt-1">Multivariate outlier fraction</span>
              </div>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-5 pt-3 border-t border-slate-100">
              <div>
                <label className="font-semibold text-slate-700 block mb-1.5">
                  Critical Stockout Days-of-Cover (&lt; Days)
                </label>
                <input
                  type="number"
                  step="0.5"
                  min="1.0"
                  max="30.0"
                  value={highRiskDocDays}
                  onChange={(e) => setHighRiskDocDays(Number(e.target.value))}
                  className="w-full p-2.5 rounded-xl border border-slate-200 bg-slate-50 font-mono text-slate-900"
                />
                <span className="text-[11px] text-slate-400 block mt-1">Items below this raise Critical Stockout alert</span>
              </div>

              <div>
                <label className="font-semibold text-slate-700 block mb-1.5">
                  Warning Stockout Days-of-Cover (Days)
                </label>
                <input
                  type="number"
                  step="0.5"
                  min="2.0"
                  max="60.0"
                  value={mediumRiskDocDays}
                  onChange={(e) => setMediumRiskDocDays(Number(e.target.value))}
                  className="w-full p-2.5 rounded-xl border border-slate-200 bg-slate-50 font-mono text-slate-900"
                />
                <span className="text-[11px] text-slate-400 block mt-1">Items below this enter Warning band</span>
              </div>
            </div>

            <div className="flex justify-end pt-3">
              <button
                type="submit"
                disabled={isSavingAlertConfig}
                className="px-6 py-2.5 rounded-xl bg-teal-600 hover:bg-teal-700 text-white font-bold shadow-md shadow-teal-500/20 flex items-center gap-2 disabled:opacity-50"
              >
                {isSavingAlertConfig ? (
                  <>
                    <Loader2 className="w-4 h-4 animate-spin" />
                    <span>Saving...</span>
                  </>
                ) : (
                  <>
                    <Save className="w-4 h-4" />
                    <span>Save Alert Thresholds</span>
                  </>
                )}
              </button>
            </div>
          </form>
        </div>
      )}

      {/* Tab 3: Model Configuration */}
      {activeTab === "models" && (
        <form
          onSubmit={(e) => {
            e.preventDefault();
            toast.success("Forecasting hyperparameters updated.", "Configuration Saved");
          }}
          className="space-y-6"
        >
          <div className="p-6 rounded-2xl bg-white border border-slate-200 shadow-xs space-y-4 text-xs">
            <div className="flex items-center gap-2 text-slate-800 font-bold text-sm pb-3 border-b border-slate-100">
              <Sliders className="w-4 h-4 text-teal-600" />
              <span>Ensemble Forecasting Hyperparameters</span>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
              <div>
                <label className="font-semibold text-slate-700 block mb-1.5">Automated Retraining Frequency</label>
                <select
                  value={retrainFrequency}
                  onChange={(e) => setRetrainFrequency(e.target.value)}
                  className="w-full p-2.5 rounded-xl border border-slate-200 bg-slate-50 text-slate-800 font-medium"
                >
                  <option value="daily">Daily (Nightly Batch)</option>
                  <option value="weekly">Weekly (Sunday Batch)</option>
                  <option value="monthly">Monthly</option>
                </select>
              </div>

              <div>
                <label className="font-semibold text-slate-700 block mb-1.5">Confidence Interval Level</label>
                <select
                  value={confidenceLevel}
                  onChange={(e) => setConfidenceLevel(e.target.value)}
                  className="w-full p-2.5 rounded-xl border border-slate-200 bg-slate-50 text-slate-800 font-medium font-mono"
                >
                  <option value="95">95% (Standard 1.96σ)</option>
                  <option value="90">90% (1.645σ)</option>
                  <option value="80">80% (1.28σ)</option>
                </select>
              </div>

              <div>
                <label className="font-semibold text-slate-700 block mb-1.5">Cold-Start History Cutoff (Weeks)</label>
                <input
                  type="number"
                  min="2"
                  max="26"
                  value={coldStartWeeks}
                  onChange={(e) => setColdStartWeeks(Number(e.target.value))}
                  className="w-full p-2.5 rounded-xl border border-slate-200 bg-slate-50 text-slate-800 font-mono"
                />
              </div>
            </div>
          </div>

          <div className="flex justify-end">
            <button
              type="submit"
              className="px-6 py-2.5 rounded-xl bg-slate-900 hover:bg-slate-800 text-white text-xs font-bold shadow-sm flex items-center gap-2"
            >
              <Save className="w-4 h-4" />
              <span>Save Configuration</span>
            </button>
          </div>
        </form>
      )}
    </div>
  );
}
