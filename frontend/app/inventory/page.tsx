"use client";

import React, { useState, useEffect } from "react";
import {
  Boxes,
  Plus,
  AlertCircle,
  CheckCircle2,
  ShoppingCart,
  Clock,
  DollarSign,
  Search,
  Filter,
  RefreshCw,
  Loader2,
  X,
} from "lucide-react";
import DataTable, { Column } from "@/components/DataTable";
import { api } from "@/lib/api";
import { ReorderRecommendationItem } from "@/types";
import { useAuth } from "@/context/AuthContext";
import { useToast } from "@/context/ToastContext";

export default function InventoryPage() {
  const { user } = useAuth();
  const toast = useToast();

  const [recommendations, setRecommendations] = useState<ReorderRecommendationItem[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [selectedStore, setSelectedStore] = useState<number | null>(user?.assigned_store_id || null);
  const [filterRisk, setFilterRisk] = useState<string>("ALL");
  const [searchQuery, setSearchQuery] = useState<string>("");

  // Modal State for PO Creation
  const [poModalItem, setPoModalItem] = useState<ReorderRecommendationItem | null>(null);
  const [orderQty, setOrderQty] = useState<number>(50);
  const [supplierName, setSupplierName] = useState<string>("Logitech Global Supply");
  const [isSubmittingPO, setIsSubmittingPO] = useState<boolean>(false);

  const fetchRecommendations = async () => {
    setLoading(true);
    try {
      const res = await api.inventory.getRecommendations(selectedStore, 50, 0);
      setRecommendations(res.items || []);
    } catch (e: any) {
      toast.error(e.message || "Failed to load inventory recommendations.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchRecommendations();
  }, [selectedStore]);

  const openPoModal = (item: ReorderRecommendationItem) => {
    setPoModalItem(item);
    setOrderQty(item.suggested_order_qty > 0 ? item.suggested_order_qty : 50);
    setSupplierName(item.category === "Displays" ? "Dell Display Solutions" : "Logitech Global Supply");
  };

  const handleCreatePO = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!poModalItem) return;

    setIsSubmittingPO(true);
    const targetItem = poModalItem;

    try {
      const res = await api.inventory.createPurchaseOrder({
        product_id: targetItem.product_id,
        store_id: targetItem.store_id,
        order_quantity: orderQty,
        supplier_name: supplierName,
      });

      toast.success(
        `Purchase Order #${res.id} submitted for ${orderQty} units ($${res.total_cost.toLocaleString()}).`,
        "Purchase Order Created"
      );

      // Optimistic UI update
      setRecommendations((prev) =>
        prev.map((item) =>
          item.product_id === targetItem.product_id && item.store_id === targetItem.store_id
            ? { ...item, risk_level: "OK" as const, suggested_order_qty: 0 }
            : item
        )
      );

      setPoModalItem(null);
    } catch (err: any) {
      toast.error(err.message || "Failed to create purchase order.");
    } finally {
      setIsSubmittingPO(false);
    }
  };

  // Filter items
  const filteredItems = recommendations.filter((item) => {
    const matchesRisk = filterRisk === "ALL" || item.risk_level === filterRisk;
    const matchesSearch =
      item.sku_code.toLowerCase().includes(searchQuery.toLowerCase()) ||
      item.product_name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      item.category.toLowerCase().includes(searchQuery.toLowerCase());
    return matchesRisk && matchesSearch;
  });

  const columns: Column<ReorderRecommendationItem>[] = [
    {
      header: "Product & SKU",
      cell: (row) => (
        <div>
          <span className="font-mono font-bold text-slate-900 block">{row.sku_code}</span>
          <span className="text-xs text-slate-700 font-medium">{row.product_name}</span>
          <span className="text-[10px] text-slate-400 font-mono block">{row.category}</span>
        </div>
      ),
    },
    {
      header: "Store Location",
      cell: (row) => (
        <span className="font-mono text-xs text-slate-600 bg-slate-100 px-2 py-0.5 rounded border">
          Store #{row.store_id}
        </span>
      ),
    },
    {
      header: "Current Stock",
      cell: (row) => (
        <div>
          <span className="font-mono font-bold text-slate-900">{row.current_stock} units</span>
          <span className="text-[11px] text-slate-400 block font-mono">
            ROP: {row.reorder_point} | Safety: {row.safety_stock}
          </span>
        </div>
      ),
    },
    {
      header: "Lead Time / Supply",
      cell: (row) => (
        <div className="text-xs">
          <span className="flex items-center gap-1 text-slate-700 font-medium">
            <Clock className="w-3.5 h-3.5 text-slate-400" />
            {row.lead_time_days} days lead
          </span>
          <span className="text-[11px] text-slate-500 font-mono">
            ~{row.days_of_supply_remaining}d supply left
          </span>
        </div>
      ),
    },
    {
      header: "Suggested Reorder",
      cell: (row) => (
        <div>
          <span className="font-mono font-bold text-teal-800">
            {row.suggested_order_qty > 0 ? `${row.suggested_order_qty} units` : "—"}
          </span>
          {row.suggested_order_qty > 0 && (
            <span className="text-[11px] text-slate-500 font-mono block">
              est. ${row.estimated_order_cost.toLocaleString()}
            </span>
          )}
        </div>
      ),
    },
    {
      header: "Risk Level",
      cell: (row) => {
        if (row.risk_level === "CRITICAL") {
          return (
            <span className="inline-flex items-center gap-1 text-[10px] font-bold uppercase tracking-wider px-2.5 py-0.5 rounded-full bg-rose-100 text-rose-800 border border-rose-300 font-mono">
              <AlertCircle className="w-3 h-3 text-rose-600" />
              Critical
            </span>
          );
        }
        if (row.risk_level === "WARNING") {
          return (
            <span className="inline-flex items-center gap-1 text-[10px] font-bold uppercase tracking-wider px-2.5 py-0.5 rounded-full bg-amber-100 text-amber-800 border border-amber-300 font-mono">
              <AlertCircle className="w-3 h-3 text-amber-600" />
              Warning
            </span>
          );
        }
        return (
          <span className="inline-flex items-center gap-1 text-[10px] font-bold uppercase tracking-wider px-2.5 py-0.5 rounded-full bg-emerald-100 text-emerald-800 border border-emerald-300 font-mono">
            <CheckCircle2 className="w-3 h-3 text-emerald-600" />
            Optimal
          </span>
        );
      },
    },
    {
      header: "Actions",
      cell: (row) => (
        <button
          onClick={() => openPoModal(row)}
          className="px-3 py-1.5 rounded-lg bg-teal-600 hover:bg-teal-700 text-white font-bold text-xs shadow-xs transition-colors flex items-center gap-1.5"
        >
          <ShoppingCart className="w-3.5 h-3.5" />
          <span>Create PO</span>
        </button>
      ),
    },
  ];

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">Inventory & Reorder Optimization</h1>
          <p className="text-xs text-slate-500 mt-1">
            Real-time stock monitoring, automated replenishment thresholds, and buffer stock calculations.
          </p>
        </div>

        <button
          onClick={fetchRecommendations}
          className="px-4 py-2.5 rounded-xl bg-white border border-slate-200 hover:bg-slate-50 text-slate-700 text-xs font-semibold flex items-center gap-2 shadow-2xs transition-all"
        >
          <RefreshCw className={`w-4 h-4 ${loading ? "animate-spin text-teal-600" : ""}`} />
          <span>Refresh Recommendations</span>
        </button>
      </div>

      {/* Filter Ribbon */}
      <div className="p-4 rounded-2xl bg-white border border-slate-200/80 shadow-xs flex flex-wrap items-center justify-between gap-4">
        {/* Search */}
        <div className="relative w-full sm:w-72">
          <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Filter by SKU or description..."
            className="w-full pl-9 pr-4 py-2 bg-slate-50 border border-slate-200 rounded-xl text-xs focus:outline-none focus:ring-2 focus:ring-teal-500/20"
          />
        </div>

        {/* Risk Level Pills */}
        <div className="flex items-center p-1 bg-slate-100 rounded-xl">
          {["ALL", "CRITICAL", "WARNING", "OK"].map((risk) => (
            <button
              key={risk}
              onClick={() => setFilterRisk(risk)}
              className={`px-3 py-1.5 rounded-lg text-xs font-semibold uppercase font-mono transition-colors ${
                filterRisk === risk ? "bg-white text-slate-900 shadow-2xs" : "text-slate-500 hover:text-slate-900"
              }`}
            >
              {risk}
            </button>
          ))}
        </div>
      </div>

      {/* Data Table */}
      <DataTable columns={columns} data={filteredItems} />

      {/* Purchase Order Modal */}
      {poModalItem && (
        <div className="fixed inset-0 z-50 bg-slate-950/70 backdrop-blur-xs flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl border border-slate-200 shadow-2xl max-w-lg w-full p-6 animate-in fade-in zoom-in-95">
            <div className="flex items-center justify-between border-b border-slate-100 pb-4 mb-5">
              <div className="flex items-center gap-2.5">
                <div className="p-2 rounded-xl bg-teal-100 text-teal-800">
                  <ShoppingCart className="w-5 h-5" />
                </div>
                <div>
                  <h3 className="font-bold text-base text-slate-900">Generate Purchase Order</h3>
                  <p className="text-xs text-slate-500 font-mono">{poModalItem.sku_code}</p>
                </div>
              </div>
              <button
                onClick={() => setPoModalItem(null)}
                className="p-1 rounded-lg text-slate-400 hover:text-slate-700 hover:bg-slate-100"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <form onSubmit={handleCreatePO} className="space-y-4 text-xs">
              <div className="p-3.5 rounded-xl bg-slate-50 border border-slate-200 grid grid-cols-2 gap-3 font-mono">
                <div>
                  <span className="text-slate-400 block text-[10px] uppercase">Product</span>
                  <span className="font-bold text-slate-800">{poModalItem.product_name}</span>
                </div>
                <div>
                  <span className="text-slate-400 block text-[10px] uppercase">Destination</span>
                  <span className="font-bold text-slate-800">Store #{poModalItem.store_id}</span>
                </div>
                <div>
                  <span className="text-slate-400 block text-[10px] uppercase">Unit Cost</span>
                  <span className="font-bold text-slate-800">${poModalItem.unit_cost.toFixed(2)}</span>
                </div>
                <div>
                  <span className="text-slate-400 block text-[10px] uppercase">Total Order Cost</span>
                  <span className="font-bold text-teal-700 text-sm">
                    ${(orderQty * poModalItem.unit_cost).toLocaleString()}
                  </span>
                </div>
              </div>

              <div>
                <label className="block font-semibold text-slate-700 uppercase tracking-wider text-[11px] font-mono mb-1.5">
                  Order Quantity (Units)
                </label>
                <input
                  type="number"
                  min="1"
                  required
                  value={orderQty}
                  onChange={(e) => setOrderQty(Number(e.target.value))}
                  className="w-full px-3.5 py-2.5 bg-slate-50 border border-slate-200 rounded-xl font-mono text-sm font-bold text-slate-900 focus:outline-none focus:ring-2 focus:ring-teal-500/20"
                />
              </div>

              <div>
                <label className="block font-semibold text-slate-700 uppercase tracking-wider text-[11px] font-mono mb-1.5">
                  Supplier Name
                </label>
                <input
                  type="text"
                  required
                  value={supplierName}
                  onChange={(e) => setSupplierName(e.target.value)}
                  className="w-full px-3.5 py-2 bg-slate-50 border border-slate-200 rounded-xl text-slate-900 focus:outline-none focus:ring-2 focus:ring-teal-500/20"
                />
              </div>

              <div className="pt-4 flex items-center justify-end gap-3">
                <button
                  type="button"
                  onClick={() => setPoModalItem(null)}
                  className="px-4 py-2 rounded-xl border border-slate-200 text-slate-600 hover:bg-slate-50 font-semibold"
                >
                  Cancel
                </button>

                <button
                  type="submit"
                  disabled={isSubmittingPO}
                  className="px-5 py-2 rounded-xl bg-teal-600 hover:bg-teal-700 text-white font-bold shadow-md shadow-teal-500/20 flex items-center gap-2 disabled:opacity-50"
                >
                  {isSubmittingPO ? (
                    <>
                      <Loader2 className="w-4 h-4 animate-spin" />
                      <span>Submitting PO...</span>
                    </>
                  ) : (
                    <>
                      <ShoppingCart className="w-4 h-4" />
                      <span>Confirm & Submit PO</span>
                    </>
                  )}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
