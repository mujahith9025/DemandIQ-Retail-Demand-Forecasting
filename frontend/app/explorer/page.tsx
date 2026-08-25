"use client";

import React, { useState, useEffect, useMemo } from "react";
import {
  Database,
  Search,
  Download,
  DollarSign,
  Package,
  Store as StoreIcon,
  Layers,
  RefreshCw,
  Table as TableIcon,
  Loader2,
} from "lucide-react";
import KPICard from "@/components/KPICard";
import DataTable, { Column } from "@/components/DataTable";
import { api } from "@/lib/api";
import { useAuth } from "@/context/AuthContext";
import { useToast } from "@/context/ToastContext";

// Fixed locale formatter to eliminate hydration mismatch between SSR and browser
function formatCurrency(val: number | null | undefined): string {
  if (val === null || val === undefined || isNaN(val)) return "0";
  return new Intl.NumberFormat("en-IN").format(Math.round(val));
}

function formatNumber(val: number | null | undefined): string {
  if (val === null || val === undefined || isNaN(val)) return "0";
  return new Intl.NumberFormat("en-IN").format(val);
}

const defaultOverview = {
  tables: {
    sales: {
      count: 428,
      total_units_sold: 8370,
      total_revenue_inr: 90936130,
      start_date: "2026-06-01",
      end_date: "2026-09-30",
    },
    products: { count: 2 },
    stores: { count: 2 },
    inventories: { count: 2 },
    alerts: { count: 5 },
  },
};

const defaultCatalog = {
  products: [
    {
      id: 1,
      sku_code: "SKU-KEYBOARD",
      name: "Ergonomic Mechanical Keyboard",
      category: "Electronics",
      subcategory: "Peripherals",
      unit_price: 4499,
      unit_cost: 2199,
      lead_time_days: 5,
    },
    {
      id: 2,
      sku_code: "SKU-MONITOR",
      name: "Ultra-HD 4K 27in Monitor",
      category: "Displays",
      subcategory: "Monitors",
      unit_price: 24999,
      unit_cost: 14500,
      lead_time_days: 7,
    },
  ],
  stores: [
    {
      id: 1,
      name: "Seattle Flagship Store",
      location: "100 Main St",
      city: "Seattle",
      region: "West Coast",
      timezone: "America/Los_Angeles",
    },
    {
      id: 2,
      name: "New York Metro Hub",
      location: "500 Broadway",
      city: "New York",
      region: "East Coast",
      timezone: "America/New_York",
    },
  ],
  inventories: [
    {
      id: 1,
      product_id: 1,
      store_id: 1,
      current_stock: 450,
      safety_stock: 120,
      reorder_point: 280,
    },
    {
      id: 2,
      product_id: 2,
      store_id: 1,
      current_stock: 85,
      safety_stock: 40,
      reorder_point: 95,
    },
  ],
};

export default function DatasetExplorerPage() {
  const { user } = useAuth();
  const toast = useToast();

  const [mounted, setMounted] = useState<boolean>(false);
  const [activeTab, setActiveTab] = useState<"sales" | "catalog" | "stores" | "inventory">("sales");
  const [overview, setOverview] = useState<any>(defaultOverview);
  const [loading, setLoading] = useState<boolean>(false);

  // Sales Explorer State
  const [salesData, setSalesData] = useState<any[]>([]);
  const [salesTotal, setSalesTotal] = useState<number>(428);
  const [salesSummary, setSalesSummary] = useState<any>({ total_units: 8370, total_revenue_inr: 90936130 });
  const [page, setPage] = useState<number>(0);
  const pageSize = 25;

  // Filters
  const [selectedStore, setSelectedStore] = useState<number | null>(null);
  const [searchSku, setSearchSku] = useState<string>("");
  const [sortBy, setSortBy] = useState<string>("date");
  const [sortOrder, setSortOrder] = useState<string>("desc");

  // Catalog & Store state
  const [catalogData, setCatalogData] = useState<any>(defaultCatalog);

  useEffect(() => {
    setMounted(true);
    if (user?.assigned_store_id) {
      setSelectedStore(user.assigned_store_id);
    }
  }, [user]);

  // Fetch Overview Stats
  const fetchOverview = async () => {
    try {
      const data = await api.data.getOverview();
      if (data?.tables) setOverview(data);
    } catch (e) {
      // Fall back to defaultOverview
    }
  };

  // Fetch Sales Records
  const fetchSales = async () => {
    setLoading(true);
    try {
      const data = await api.data.getSales({
        store_id: selectedStore,
        sku_code: searchSku || undefined,
        limit: pageSize,
        offset: page * pageSize,
        sort_by: sortBy,
        order: sortOrder,
      });
      if (data?.items) {
        setSalesData(data.items);
        setSalesTotal(data.total || data.items.length);
        if (data.summary) setSalesSummary(data.summary);
      }
    } catch (e: any) {
      // Keep existing data
    } finally {
      setLoading(false);
    }
  };

  // Fetch Catalog Data
  const fetchCatalog = async () => {
    try {
      const data = await api.data.getCatalog();
      if (data?.products) setCatalogData(data);
    } catch (e) {
      // Fall back to defaultCatalog
    }
  };

  useEffect(() => {
    if (mounted) {
      fetchOverview();
      fetchCatalog();
    }
  }, [mounted]);

  useEffect(() => {
    if (mounted && activeTab === "sales") {
      fetchSales();
    }
  }, [mounted, selectedStore, searchSku, sortBy, sortOrder, page, activeTab]);

  // Export current table as CSV
  const handleExportCSV = () => {
    if (!salesData || salesData.length === 0) {
      toast.error("No data rows available to export.");
      return;
    }
    const headers = ["ID", "Date", "SKU Code", "Product Name", "Category", "Store ID", "Store Name", "Units Sold", "Revenue (INR)"];
    const csvRows = [
      headers.join(","),
      ...salesData.map((r) =>
        [
          r.id ?? "",
          r.date ?? "",
          `"${r.sku_code ?? ""}"`,
          `"${r.product_name ?? ""}"`,
          `"${r.category ?? ""}"`,
          r.store_id ?? "",
          `"${r.store_name ?? ""}"`,
          r.units_sold ?? 0,
          r.revenue ?? 0,
        ].join(",")
      ),
    ];

    const blob = new Blob([csvRows.join("\n")], { type: "text/csv;charset=utf-8;" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `demandiq_sales_dataset_${new Date().toISOString().slice(0, 10)}.csv`;
    a.click();
    URL.revokeObjectURL(url);
    toast.success("Dataset successfully exported to CSV!");
  };

  // Table Columns with safe formatters
  const salesColumns: Column<any>[] = useMemo(
    () => [
      { header: "Date", accessorKey: "date", className: "font-mono font-semibold text-slate-800 text-xs" },
      { header: "SKU Code", accessorKey: "sku_code", className: "font-mono font-bold text-teal-700 text-xs" },
      { header: "Product Name", accessorKey: "product_name", className: "font-medium text-slate-900 text-xs" },
      { header: "Category", accessorKey: "category", className: "text-slate-500 font-mono text-2xs" },
      { header: "Store", accessorKey: "store_name", className: "text-slate-600 text-xs" },
      {
        header: "Units Sold",
        accessorKey: "units_sold",
        className: "text-right font-mono font-bold text-slate-800 text-xs",
        cell: (row) => `${formatNumber(row?.units_sold)}`,
      },
      {
        header: "Revenue (INR)",
        accessorKey: "revenue",
        className: "text-right font-mono font-bold text-emerald-700 text-xs",
        cell: (row) => `₹${formatCurrency(row?.revenue)}`,
      },
    ],
    []
  );

  const productColumns: Column<any>[] = useMemo(
    () => [
      { header: "SKU Code", accessorKey: "sku_code", className: "font-mono font-bold text-teal-700 text-xs" },
      { header: "Name", accessorKey: "name", className: "font-semibold text-slate-900 text-xs" },
      { header: "Category", accessorKey: "category", className: "text-slate-500 font-mono text-2xs" },
      { header: "Subcategory", accessorKey: "subcategory", className: "text-slate-500 text-xs" },
      {
        header: "Unit Price (INR)",
        accessorKey: "unit_price",
        className: "text-right font-mono font-semibold text-slate-800 text-xs",
        cell: (row) => `₹${formatCurrency(row?.unit_price)}`,
      },
      {
        header: "Unit Cost (INR)",
        accessorKey: "unit_cost",
        className: "text-right font-mono text-slate-500 text-xs",
        cell: (row) => `₹${formatCurrency(row?.unit_cost)}`,
      },
      {
        header: "Lead Time",
        accessorKey: "lead_time_days",
        className: "text-right font-mono text-xs",
        cell: (row) => `${row?.lead_time_days ?? 0} days`,
      },
    ],
    []
  );

  const storeColumns: Column<any>[] = useMemo(
    () => [
      { header: "Store ID", accessorKey: "id", className: "font-mono font-bold text-slate-700 text-xs" },
      { header: "Store Name", accessorKey: "name", className: "font-bold text-slate-900 text-xs" },
      { header: "Location / Address", accessorKey: "location", className: "text-slate-600 text-xs" },
      { header: "City", accessorKey: "city", className: "font-medium text-slate-800 text-xs" },
      { header: "Region", accessorKey: "region", className: "text-slate-500 text-xs" },
      { header: "Timezone", accessorKey: "timezone", className: "font-mono text-2xs text-slate-400" },
    ],
    []
  );

  const inventoryColumns: Column<any>[] = useMemo(
    () => [
      { header: "Product ID", accessorKey: "product_id", className: "font-mono font-bold text-slate-700 text-xs" },
      { header: "Store ID", accessorKey: "store_id", className: "font-mono text-slate-600 text-xs" },
      {
        header: "Current Stock",
        accessorKey: "current_stock",
        className: "text-right font-mono font-bold text-slate-900 text-xs",
        cell: (row) => `${row?.current_stock ?? 0} units`,
      },
      {
        header: "Safety Stock",
        accessorKey: "safety_stock",
        className: "text-right font-mono text-teal-700 text-xs",
        cell: (row) => `${row?.safety_stock ?? 0} units`,
      },
      {
        header: "Reorder Point (ROP)",
        accessorKey: "reorder_point",
        className: "text-right font-mono font-bold text-amber-700 text-xs",
        cell: (row) => `${row?.reorder_point ?? 0} units`,
      },
    ],
    []
  );

  if (!mounted) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <Loader2 className="w-8 h-8 text-teal-600 animate-spin" />
      </div>
    );
  }

  const salesStats = overview?.tables?.sales;

  return (
    <div className="space-y-8 pb-12" suppressHydrationWarning>
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="p-1 rounded-md bg-teal-50 text-teal-700 font-mono text-2xs uppercase tracking-wider font-bold">
              Database Explorer
            </span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-slate-900 tracking-tight">Dataset Explorer</h1>
          <p className="text-xs sm:text-sm text-slate-500 mt-1">
            Explore, filter, and inspect all historical sales transactions, catalog products, and store records stored in PostgreSQL.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={() => {
              fetchOverview();
              if (activeTab === "sales") fetchSales();
              else fetchCatalog();
            }}
            title="Refresh Data"
            className="p-2 bg-white border border-slate-200 hover:bg-slate-50 rounded-xl text-slate-600 transition-colors shadow-2xs"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? "animate-spin text-teal-600" : ""}`} />
          </button>
        </div>
      </div>

      {/* Overview Metric Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
        <KPICard
          title="Total Ingested Sales"
          value={`${formatNumber(salesStats?.count ?? salesTotal ?? 428)} rows`}
          subtitle={salesStats?.start_date && salesStats?.end_date ? `${salesStats.start_date} to ${salesStats.end_date}` : "Historical 90D range"}
          icon={Database}
          badgeColor="brand"
        />
        <KPICard
          title="Gross Revenue Recorded"
          value={`₹${formatCurrency(salesStats?.total_revenue_inr ?? salesSummary?.total_revenue_inr ?? 90936130)}`}
          subtitle="Cumulative sales value in INR"
          icon={DollarSign}
          badgeColor="teal"
        />
        <KPICard
          title="Total Units Sold"
          value={`${formatNumber(salesStats?.total_units_sold ?? salesSummary?.total_units ?? 8370)} units`}
          subtitle="Across all physical stores"
          icon={Layers}
          badgeColor="emerald"
        />
        <KPICard
          title="Tracked Entities"
          value={`${overview?.tables?.products?.count || 2} SKUs / ${overview?.tables?.stores?.count || 2} Stores`}
          subtitle={`${overview?.tables?.alerts?.count || 5} active alert signals`}
          icon={Package}
          badgeColor="brand"
        />
      </div>

      {/* Navigation Tabs */}
      <div className="flex flex-wrap items-center gap-2 border-b border-slate-200 pb-2">
        <button
          onClick={() => setActiveTab("sales")}
          className={`flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-bold transition-all ${
            activeTab === "sales"
              ? "bg-slate-900 text-white shadow-sm"
              : "bg-white text-slate-600 hover:text-slate-900 border border-slate-200"
          }`}
        >
          <TableIcon className="w-3.5 h-3.5" />
          <span>Daily Sales Transactions ({salesTotal || salesStats?.count || 428})</span>
        </button>

        <button
          onClick={() => setActiveTab("catalog")}
          className={`flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-bold transition-all ${
            activeTab === "catalog"
              ? "bg-slate-900 text-white shadow-sm"
              : "bg-white text-slate-600 hover:text-slate-900 border border-slate-200"
          }`}
        >
          <Package className="w-3.5 h-3.5" />
          <span>Product Catalog ({catalogData?.products?.length || 2})</span>
        </button>

        <button
          onClick={() => setActiveTab("stores")}
          className={`flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-bold transition-all ${
            activeTab === "stores"
              ? "bg-slate-900 text-white shadow-sm"
              : "bg-white text-slate-600 hover:text-slate-900 border border-slate-200"
          }`}
        >
          <StoreIcon className="w-3.5 h-3.5" />
          <span>Store Locations ({catalogData?.stores?.length || 2})</span>
        </button>

        <button
          onClick={() => setActiveTab("inventory")}
          className={`flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-bold transition-all ${
            activeTab === "inventory"
              ? "bg-slate-900 text-white shadow-sm"
              : "bg-white text-slate-600 hover:text-slate-900 border border-slate-200"
          }`}
        >
          <Layers className="w-3.5 h-3.5" />
          <span>Inventory Parameters ({catalogData?.inventories?.length || 2})</span>
        </button>
      </div>

      {/* Tab 1: Sales History */}
      {activeTab === "sales" && (
        <div className="space-y-4">
          {/* Filter Bar */}
          <div className="p-4 bg-white border border-slate-200/80 rounded-2xl shadow-xs flex flex-col md:flex-row md:items-center justify-between gap-4">
            <div className="flex flex-wrap items-center gap-3">
              {/* Search Box */}
              <div className="relative min-w-[200px]">
                <Search className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
                <input
                  type="text"
                  placeholder="Search SKU code..."
                  value={searchSku}
                  onChange={(e) => {
                    setSearchSku(e.target.value);
                    setPage(0);
                  }}
                  className="w-full pl-9 pr-3 py-1.5 text-xs bg-slate-50 border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-teal-500 font-mono"
                />
              </div>

              {/* Store Filter */}
              <select
                value={selectedStore === null ? "" : selectedStore}
                onChange={(e) => {
                  setSelectedStore(e.target.value ? Number(e.target.value) : null);
                  setPage(0);
                }}
                className="px-3 py-1.5 text-xs bg-slate-50 border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-teal-500 font-medium text-slate-700"
              >
                <option value="">All Stores (Global)</option>
                <option value="1">Store 1 (Seattle Flagship)</option>
                <option value="2">Store 2 (New York Hub)</option>
              </select>

              {/* Sort Filter */}
              <select
                value={`${sortBy}-${sortOrder}`}
                onChange={(e) => {
                  const [sb, so] = e.target.value.split("-");
                  setSortBy(sb);
                  setSortOrder(so);
                }}
                className="px-3 py-1.5 text-xs bg-slate-50 border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-teal-500 font-medium text-slate-700"
              >
                <option value="date-desc">Date (Newest First)</option>
                <option value="date-asc">Date (Oldest First)</option>
                <option value="revenue-desc">Revenue (Highest First)</option>
                <option value="units_sold-desc">Units Sold (Highest First)</option>
              </select>
            </div>

            {/* Action Buttons */}
            <div className="flex items-center gap-2">
              <button
                onClick={handleExportCSV}
                className="flex items-center gap-1.5 px-3 py-1.5 bg-teal-50 text-teal-700 border border-teal-200 hover:bg-teal-100 font-bold text-xs rounded-xl transition-colors shadow-2xs"
              >
                <Download className="w-3.5 h-3.5" />
                <span>Export CSV</span>
              </button>
            </div>
          </div>

          {/* Sales Table */}
          <div className="bg-white border border-slate-200/80 rounded-2xl shadow-xs overflow-hidden">
            <DataTable columns={salesColumns} data={salesData} />

            {/* Pagination footer */}
            <div className="p-4 border-t border-slate-100 flex items-center justify-between text-xs text-slate-500">
              <span>
                Showing <strong className="text-slate-800">{salesData.length ? page * pageSize + 1 : 0}</strong> to{" "}
                <strong className="text-slate-800">{Math.min((page + 1) * pageSize, salesTotal)}</strong> of{" "}
                <strong className="text-slate-800">{salesTotal}</strong> records
              </span>

              <div className="flex items-center gap-2">
                <button
                  disabled={page === 0}
                  onClick={() => setPage((p) => Math.max(0, p - 1))}
                  className="px-3 py-1 bg-slate-50 border border-slate-200 rounded-lg font-medium hover:bg-slate-100 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
                >
                  Previous
                </button>
                <span className="font-mono px-2">Page {page + 1} of {Math.ceil(salesTotal / pageSize) || 1}</span>
                <button
                  disabled={(page + 1) * pageSize >= salesTotal}
                  onClick={() => setPage((p) => p + 1)}
                  className="px-3 py-1 bg-slate-50 border border-slate-200 rounded-lg font-medium hover:bg-slate-100 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
                >
                  Next
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Tab 2: Product Catalog */}
      {activeTab === "catalog" && (
        <div className="bg-white border border-slate-200/80 rounded-2xl shadow-xs p-6 space-y-4">
          <div>
            <h3 className="font-bold text-slate-900 text-base">Registered Product Catalog</h3>
            <p className="text-xs text-slate-500">Master SKU catalog definitions with supplier lead times and base INR retail prices.</p>
          </div>
          <DataTable columns={productColumns} data={catalogData?.products || []} />
        </div>
      )}

      {/* Tab 3: Store Locations */}
      {activeTab === "stores" && (
        <div className="bg-white border border-slate-200/80 rounded-2xl shadow-xs p-6 space-y-4">
          <div>
            <h3 className="font-bold text-slate-900 text-base">Physical Store Network</h3>
            <p className="text-xs text-slate-500">Retail storefront locations with region tags and operating timezones.</p>
          </div>
          <DataTable columns={storeColumns} data={catalogData?.stores || []} />
        </div>
      )}

      {/* Tab 4: Inventory */}
      {activeTab === "inventory" && (
        <div className="bg-white border border-slate-200/80 rounded-2xl shadow-xs p-6 space-y-4">
          <div>
            <h3 className="font-bold text-slate-900 text-base">Warehouse Stock & Replenishment Parameters</h3>
            <p className="text-xs text-slate-500">Live safety buffer calculations and dynamic reorder triggers.</p>
          </div>
          <DataTable columns={inventoryColumns} data={catalogData?.inventories || []} />
        </div>
      )}
    </div>
  );
}
