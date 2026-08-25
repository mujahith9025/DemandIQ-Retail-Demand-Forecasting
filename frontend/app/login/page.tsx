"use client";

import React, { useState } from "react";
import { useAuth } from "@/context/AuthContext";
import { useRouter } from "next/navigation";
import { Zap, Lock, Mail, ArrowRight, Shield, Building2, AlertCircle, Loader2 } from "lucide-react";
import { useToast } from "@/context/ToastContext";

export default function LoginPage() {
  const [email, setEmail] = useState("planner@demandiq.io");
  const [password, setPassword] = useState("plannerpassword123");
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const { login } = useAuth();
  const router = useRouter();
  const toast = useToast();

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMsg(null);
    setIsSubmitting(true);

    try {
      await login(email, password);
      toast.success("Successfully signed in to DemandIQ.", "Welcome Back");
      router.push("/dashboard");
    } catch (err: any) {
      setErrorMsg(err.message || "Failed to authenticate. Please check credentials.");
      toast.error(err.message || "Invalid credentials", "Authentication Failed");
    } finally {
      setIsSubmitting(false);
    }
  };

  const setPreset = (presetEmail: string, presetPass: string) => {
    setEmail(presetEmail);
    setPassword(presetPass);
    setErrorMsg(null);
  };

  return (
    <div className="min-h-screen bg-slate-950 flex flex-col justify-center items-center p-6 select-none relative overflow-hidden">
      {/* Ambient background glows */}
      <div className="absolute top-1/4 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[350px] bg-teal-500/10 rounded-full blur-3xl pointer-events-none"></div>
      <div className="absolute bottom-10 right-10 w-96 h-96 bg-brand-600/10 rounded-full blur-3xl pointer-events-none"></div>

      <div className="w-full max-w-md relative z-10">
        {/* Brand Header */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-14 h-14 rounded-2xl bg-gradient-to-tr from-brand-700 via-teal-500 to-teal-300 shadow-xl shadow-teal-500/20 ring-1 ring-white/20 mb-4">
            <Zap className="w-7 h-7 text-white fill-white" />
          </div>
          <h1 className="text-2xl font-bold text-white tracking-tight">
            Sign in to Demand<span className="text-teal-400">IQ</span>
          </h1>
          <p className="text-xs text-slate-400 mt-1">
            Intelligent Retail Demand Forecasting & Inventory Optimization
          </p>
        </div>

        {/* Login Card */}
        <div className="bg-slate-900/80 backdrop-blur-xl border border-slate-800 rounded-2xl p-8 shadow-2xl">
          {errorMsg && (
            <div className="mb-6 p-3 rounded-xl bg-rose-500/10 border border-rose-500/30 text-rose-300 text-xs flex items-start gap-2.5">
              <AlertCircle className="w-4 h-4 shrink-0 mt-0.5 text-rose-400" />
              <span>{errorMsg}</span>
            </div>
          )}

          <form onSubmit={handleLogin} className="space-y-4">
            <div>
              <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-1.5 font-mono">
                Corporate Email
              </label>
              <div className="relative">
                <Mail className="w-4 h-4 absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-500" />
                <input
                  type="email"
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="name@demandiq.io"
                  className="w-full pl-10 pr-4 py-2.5 bg-slate-950/70 border border-slate-700/80 rounded-xl text-white text-xs placeholder:text-slate-500 focus:outline-none focus:ring-2 focus:ring-teal-500/30 focus:border-teal-400 transition-all font-mono"
                />
              </div>
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-1.5 font-mono">
                Password
              </label>
              <div className="relative">
                <Lock className="w-4 h-4 absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-500" />
                <input
                  type="password"
                  required
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••••••••"
                  className="w-full pl-10 pr-4 py-2.5 bg-slate-950/70 border border-slate-700/80 rounded-xl text-white text-xs placeholder:text-slate-500 focus:outline-none focus:ring-2 focus:ring-teal-500/30 focus:border-teal-400 transition-all font-mono"
                />
              </div>
            </div>

            <button
              type="submit"
              disabled={isSubmitting}
              className="w-full mt-2 py-3 px-4 rounded-xl bg-gradient-to-r from-teal-500 to-teal-600 hover:from-teal-400 hover:to-teal-500 text-slate-950 font-bold text-xs shadow-lg shadow-teal-500/25 transition-all flex items-center justify-center gap-2 group disabled:opacity-50"
            >
              {isSubmitting ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin text-slate-950" />
                  <span>Authenticating...</span>
                </>
              ) : (
                <>
                  <span>Sign In to Workspace</span>
                  <ArrowRight className="w-4 h-4 group-hover:translate-x-0.5 transition-transform" />
                </>
              )}
            </button>
          </form>

          {/* Quick 1-Click Role Presets for Pair Programming / Evaluation */}
          <div className="mt-8 pt-6 border-t border-slate-800/80">
            <p className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider font-mono mb-3 text-center">
              Quick 1-Click Role Presets
            </p>
            <div className="grid grid-cols-3 gap-2">
              <button
                type="button"
                onClick={() => setPreset("admin@demandiq.io", "adminpassword123")}
                className="p-2 rounded-lg bg-slate-800/50 hover:bg-slate-800 border border-slate-700/60 text-slate-300 text-[11px] font-medium flex flex-col items-center gap-1 transition-all"
              >
                <Shield className="w-3.5 h-3.5 text-purple-400" />
                <span>Admin</span>
              </button>

              <button
                type="button"
                onClick={() => setPreset("planner@demandiq.io", "plannerpassword123")}
                className="p-2 rounded-lg bg-slate-800/50 hover:bg-slate-800 border border-slate-700/60 text-slate-300 text-[11px] font-medium flex flex-col items-center gap-1 transition-all"
              >
                <Zap className="w-3.5 h-3.5 text-teal-400" />
                <span>Planner</span>
              </button>

              <button
                type="button"
                onClick={() => setPreset("manager_store1@demandiq.io", "managerpassword123")}
                className="p-2 rounded-lg bg-slate-800/50 hover:bg-slate-800 border border-slate-700/60 text-slate-300 text-[11px] font-medium flex flex-col items-center gap-1 transition-all"
              >
                <Building2 className="w-3.5 h-3.5 text-amber-400" />
                <span>Store 1 Mgr</span>
              </button>
            </div>
          </div>
        </div>

        <p className="text-center text-[11px] text-slate-500 mt-6">
          DemandIQ v1.0 • Enterprise Demand Planning
        </p>
      </div>
    </div>
  );
}
