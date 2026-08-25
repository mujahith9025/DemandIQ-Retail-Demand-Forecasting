"use client";

import React, { useState } from "react";
import { Search, Bell, ShieldCheck, ChevronDown, LogOut, User, Store as StoreIcon } from "lucide-react";
import { useAuth } from "@/context/AuthContext";
import Link from "next/link";

export default function Navbar() {
  const { user, logout } = useAuth();
  const [isDropdownOpen, setIsDropdownOpen] = useState(false);

  const getInitials = (name?: string) => {
    if (!name) return "DU";
    const parts = name.split(" ");
    if (parts.length >= 2) return `${parts[0][0]}${parts[1][0]}`.toUpperCase();
    return name.slice(0, 2).toUpperCase();
  };

  return (
    <header className="h-16 bg-white border-b border-slate-200/80 px-6 flex items-center justify-between shadow-xs sticky top-0 z-30">
      {/* Search & Global Filter */}
      <div className="flex items-center gap-4 flex-1 max-w-lg">
        <div className="relative w-full">
          <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
          <input
            type="text"
            placeholder="Search SKUs, categories, or forecast reports..."
            className="w-full pl-9 pr-4 py-2 text-xs bg-slate-50 border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-teal-500/20 focus:border-teal-600 transition-all"
          />
        </div>
      </div>

      {/* Right Action Icons & Profile */}
      <div className="flex items-center gap-4">
        {/* Store Indicator */}
        {user?.assigned_store_id ? (
          <div className="hidden sm:flex items-center gap-1.5 px-3 py-1 rounded-lg bg-amber-50 text-amber-800 border border-amber-200 text-xs font-medium font-mono">
            <StoreIcon className="w-3.5 h-3.5 text-amber-600" />
            <span>Store #{user.assigned_store_id}</span>
          </div>
        ) : (
          <div className="hidden sm:flex items-center gap-1.5 px-3 py-1 rounded-lg bg-slate-100 text-slate-700 border border-slate-200 text-xs font-medium">
            <ShieldCheck className="w-3.5 h-3.5 text-teal-600" />
            <span>Global View (All Stores)</span>
          </div>
        )}

        {/* Notifications Link */}
        <Link
          href="/alerts"
          title="Active Alerts"
          className="relative p-2 rounded-lg hover:bg-slate-100 text-slate-600 transition-colors"
        >
          <Bell className="w-4 h-4" />
          <span className="absolute top-1.5 right-1.5 w-2 h-2 rounded-full bg-rose-500 ring-2 ring-white"></span>
        </Link>

        <div className="h-6 w-px bg-slate-200 mx-1"></div>

        {/* User Profile Dropdown */}
        <div className="relative">
          <button
            onClick={() => setIsDropdownOpen(!isDropdownOpen)}
            className="flex items-center gap-2.5 pl-1 rounded-lg hover:bg-slate-50 p-1.5 transition-colors group"
          >
            <div className="w-8 h-8 rounded-full bg-slate-900 text-teal-400 border border-slate-700 flex items-center justify-center font-bold text-xs shadow-xs">
              {getInitials(user?.name)}
            </div>
            <div className="hidden md:block text-left text-xs">
              <p className="font-semibold text-slate-800 leading-none">{user?.name || "DemandIQ User"}</p>
              <p className="text-slate-400 text-[10px] mt-0.5 uppercase font-mono tracking-wider">
                {user?.role?.replace("_", " ") || "Planner"}
              </p>
            </div>
            <ChevronDown className="w-3.5 h-3.5 text-slate-400 group-hover:text-slate-600 transition-colors" />
          </button>

          {isDropdownOpen && (
            <div className="absolute right-0 mt-2 w-48 rounded-xl bg-white border border-slate-200 shadow-xl py-1.5 z-50 animate-in fade-in slide-in-from-top-1">
              <div className="px-3.5 py-2 border-b border-slate-100">
                <p className="text-xs font-semibold text-slate-800">{user?.name}</p>
                <p className="text-[11px] text-slate-400 truncate">{user?.email}</p>
              </div>

              <Link
                href="/settings"
                onClick={() => setIsDropdownOpen(false)}
                className="flex items-center gap-2 px-3.5 py-2 text-xs text-slate-700 hover:bg-slate-50 transition-colors"
              >
                <User className="w-3.5 h-3.5 text-slate-400" />
                <span>Account & Settings</span>
              </Link>

              <button
                onClick={() => {
                  setIsDropdownOpen(false);
                  logout();
                }}
                className="w-full flex items-center gap-2 px-3.5 py-2 text-xs text-rose-600 hover:bg-rose-50 transition-colors text-left"
              >
                <LogOut className="w-3.5 h-3.5 text-rose-500" />
                <span>Sign Out</span>
              </button>
            </div>
          )}
        </div>
      </div>
    </header>
  );
}
