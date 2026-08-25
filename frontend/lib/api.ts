import {
  HealthCheckResponse,
  AuthResponse,
  RefreshTokenResponse,
  User,
  ForecastPredictionResponse,
  ForecastAccuracyResponse,
  ReorderRecommendationItem,
  PurchaseOrder,
  Alert,
  SimulatePromoResponse,
  ReportItem,
  DashboardKPIs,
  PaginatedResult,
  DataUploadSuccessResponse,
  DataUploadErrorResponse,
} from "@/types";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

let isRefreshing = false;
let refreshSubscribers: Array<(token: string) => void> = [];

function subscribeTokenRefresh(cb: (token: string) => void) {
  refreshSubscribers.push(cb);
}

function onRefreshed(token: string) {
  refreshSubscribers.forEach((cb) => cb(token));
  refreshSubscribers = [];
}

export function getStoredToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem("demandiq_access_token");
}

export function getStoredRefreshToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem("demandiq_refresh_token");
}

export function setStoredTokens(accessToken: string, refreshToken?: string, user?: User) {
  if (typeof window === "undefined") return;
  localStorage.setItem("demandiq_access_token", accessToken);
  if (refreshToken) localStorage.setItem("demandiq_refresh_token", refreshToken);
  if (user) localStorage.setItem("demandiq_user", JSON.stringify(user));
}

export function clearStoredTokens() {
  if (typeof window === "undefined") return;
  localStorage.removeItem("demandiq_access_token");
  localStorage.removeItem("demandiq_refresh_token");
  localStorage.removeItem("demandiq_user");
}

export function getStoredUser(): User | null {
  if (typeof window === "undefined") return null;
  const raw = localStorage.getItem("demandiq_user");
  if (!raw) return null;
  try {
    return JSON.parse(raw);
  } catch {
    return null;
  }
}

async function fetchWithAuth<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  const url = `${API_BASE}${endpoint}`;
  let token = getStoredToken();

  const headers = new Headers(options.headers || {});
  if (!headers.has("Content-Type") && !(options.body instanceof FormData)) {
    headers.set("Content-Type", "application/json");
  }
  if (token && !headers.has("Authorization")) {
    headers.set("Authorization", `Bearer ${token}`);
  }

  let response = await fetch(url, { ...options, headers });

  // 401 Interceptor: Auto refresh token
  if (response.status === 401 && !endpoint.includes("/auth/")) {
    const refreshToken = getStoredRefreshToken();
    if (!refreshToken) {
      clearStoredTokens();
      if (typeof window !== "undefined" && window.location.pathname !== "/login") {
        window.location.href = "/login";
      }
      throw new Error("Session expired. Please log in again.");
    }

    if (!isRefreshing) {
      isRefreshing = true;
      try {
        const refreshRes = await fetch(`${API_BASE}/api/auth/refresh`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ refresh_token: refreshToken }),
        });

        if (!refreshRes.ok) {
          throw new Error("Refresh token invalid or expired.");
        }

        const refreshData: RefreshTokenResponse = await refreshRes.json();
        setStoredTokens(refreshData.access_token);
        isRefreshing = false;
        onRefreshed(refreshData.access_token);
      } catch (err) {
        isRefreshing = false;
        clearStoredTokens();
        if (typeof window !== "undefined" && window.location.pathname !== "/login") {
          window.location.href = "/login";
        }
        throw new Error("Session expired. Please log in again.");
      }
    }

    // Wait for refreshed token and retry request
    const newToken = await new Promise<string>((resolve) => {
      subscribeTokenRefresh((token) => resolve(token));
    });

    headers.set("Authorization", `Bearer ${newToken}`);
    response = await fetch(url, { ...options, headers });
  }

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(
      errorData.detail || errorData.message || `API error (${response.status}): ${response.statusText}`
    );
  }

  return response.json();
}

export const api = {
  // Auth
  auth: {
    login: async (email: string, password: string): Promise<AuthResponse> => {
      const res = await fetchWithAuth<AuthResponse>("/api/auth/login", {
        method: "POST",
        body: JSON.stringify({ email, password }),
      });
      setStoredTokens(res.access_token, res.refresh_token, res.user);
      return res;
    },

    register: async (userData: {
      name: string;
      email: string;
      password: string;
      role: string;
      assigned_store_id?: number | null;
    }): Promise<User> => {
      return fetchWithAuth<User>("/api/auth/register", {
        method: "POST",
        body: JSON.stringify(userData),
      });
    },

    refresh: async (refreshToken: string): Promise<RefreshTokenResponse> => {
      return fetchWithAuth<RefreshTokenResponse>("/api/auth/refresh", {
        method: "POST",
        body: JSON.stringify({ refresh_token: refreshToken }),
      });
    },

    logout: () => {
      clearStoredTokens();
    },
  },

  // Health
  getHealth: (): Promise<HealthCheckResponse> => fetchWithAuth<HealthCheckResponse>("/health"),
  health: {
    get: (): Promise<HealthCheckResponse> => fetchWithAuth<HealthCheckResponse>("/health"),
  },

  // Dashboard
  dashboard: {
    getKPIs: (storeId?: number | null): Promise<DashboardKPIs> => {
      const q = storeId ? `?store_id=${storeId}` : "";
      return fetchWithAuth<DashboardKPIs>(`/api/dashboard/kpis${q}`);
    },
  },

  // Demand Forecasting
  forecasts: {
    getForecast: (
      productId: number,
      storeId?: number | null,
      horizonWeeks: number = 4,
      modelType: string = "ensemble"
    ): Promise<ForecastPredictionResponse> => {
      const params = new URLSearchParams();
      if (storeId) params.append("store_id", storeId.toString());
      params.append("horizon_weeks", horizonWeeks.toString());
      params.append("model_type", modelType);
      return fetchWithAuth<ForecastPredictionResponse>(`/api/forecast/${productId}?${params.toString()}`);
    },

    getAccuracy: (productId: number, storeId: number): Promise<ForecastAccuracyResponse> => {
      return fetchWithAuth<ForecastAccuracyResponse>(
        `/api/forecast/accuracy?product_id=${productId}&store_id=${storeId}`
      );
    },

    retrain: (horizonWeeks: number = 4): Promise<any> => {
      return fetchWithAuth<any>(`/api/forecast/retrain?horizon_weeks=${horizonWeeks}`, {
        method: "POST",
      });
    },
  },

  // Inventory
  inventory: {
    getRecommendations: (
      storeId?: number | null,
      limit: number = 20,
      offset: number = 0
    ): Promise<PaginatedResult<ReorderRecommendationItem>> => {
      const params = new URLSearchParams();
      if (storeId) params.append("store_id", storeId.toString());
      params.append("limit", limit.toString());
      params.append("offset", offset.toString());
      return fetchWithAuth<PaginatedResult<ReorderRecommendationItem>>(
        `/api/inventory/recommendations?${params.toString()}`
      );
    },

    createPurchaseOrder: (data: {
      product_id: number;
      store_id: number;
      order_quantity: number;
      supplier_name?: string;
      expected_delivery_date?: string;
    }): Promise<PurchaseOrder> => {
      return fetchWithAuth<PurchaseOrder>("/api/inventory/purchase-order", {
        method: "POST",
        body: JSON.stringify(data),
      });
    },
  },

  // Alerts
  alerts: {
    getAlerts: (
      severity?: string,
      status?: string,
      limit: number = 50,
      offset: number = 0
    ): Promise<PaginatedResult<Alert>> => {
      const params = new URLSearchParams();
      if (severity && severity !== "all") params.append("severity", severity);
      if (status && status !== "all") params.append("status", status);
      params.append("limit", limit.toString());
      params.append("offset", offset.toString());
      return fetchWithAuth<PaginatedResult<Alert>>(`/api/alerts?${params.toString()}`);
    },

    patchAlert: (id: number, status: "new" | "acknowledged" | "dismissed"): Promise<Alert> => {
      return fetchWithAuth<Alert>(`/api/alerts/${id}`, {
        method: "PATCH",
        body: JSON.stringify({ status }),
      });
    },

    getConfig: (): Promise<any> => {
      return fetchWithAuth<any>("/api/alerts/config");
    },

    updateConfig: (config: any): Promise<any> => {
      return fetchWithAuth<any>("/api/alerts/config", {
        method: "POST",
        body: JSON.stringify(config),
      });
    },

    triggerScan: (targetDate?: string): Promise<any> => {
      const q = targetDate ? `?target_date=${targetDate}` : "";
      return fetchWithAuth<any>(`/api/alerts/scan${q}`, {
        method: "POST",
      });
    },
  },

  // Reports & Analytics
  reports: {
    getReports: (limit: number = 20, offset: number = 0): Promise<PaginatedResult<ReportItem>> => {
      return fetchWithAuth<PaginatedResult<ReportItem>>(`/api/reports?limit=${limit}&offset=${offset}`);
    },

    exportReport: async (type: string, format: string, storeId?: number | null): Promise<Blob> => {
      const params = new URLSearchParams();
      params.append("type", type);
      params.append("format", format);
      if (storeId) params.append("store_id", storeId.toString());

      const token = getStoredToken();
      const headers = new Headers();
      if (token) headers.set("Authorization", `Bearer ${token}`);

      const res = await fetch(`${API_BASE}/api/reports/export?${params.toString()}`, {
        method: "POST",
        headers,
      });

      if (!res.ok) throw new Error("Report export failed.");
      return await res.blob();
    },
  },

  // What-If Simulation
  simulation: {
    simulatePromo: (data: {
      product_id?: number;
      category?: string;
      discount_pct: number;
      promo_duration_days: number;
      store_id?: number | null;
    }): Promise<SimulatePromoResponse> => {
      return fetchWithAuth<SimulatePromoResponse>("/api/simulate", {
        method: "POST",
        body: JSON.stringify(data),
      });
    },
  },

  // Data Ingestion & Explorer
  data: {
    uploadSalesCSV: async (file: File): Promise<DataUploadSuccessResponse> => {
      const formData = new FormData();
      formData.append("file", file);

      const token = getStoredToken();
      const headers = new Headers();
      if (token) headers.set("Authorization", `Bearer ${token}`);

      const res = await fetch(`${API_BASE}/api/data/upload`, {
        method: "POST",
        headers,
        body: formData,
      });

      const data = await res.json();
      if (!res.ok) {
        const error: DataUploadErrorResponse = data;
        throw error;
      }
      return data;
    },

    getOverview: async (): Promise<any> => {
      return fetchWithAuth<any>("/api/data/overview");
    },

    getSales: async (params: {
      store_id?: number | null;
      sku_code?: string;
      start_date?: string;
      end_date?: string;
      limit?: number;
      offset?: number;
      sort_by?: string;
      order?: string;
    } = {}): Promise<any> => {
      const q = new URLSearchParams();
      if (params.store_id) q.set("store_id", params.store_id.toString());
      if (params.sku_code) q.set("sku_code", params.sku_code);
      if (params.start_date) q.set("start_date", params.start_date);
      if (params.end_date) q.set("end_date", params.end_date);
      if (params.limit) q.set("limit", params.limit.toString());
      if (params.offset !== undefined) q.set("offset", params.offset.toString());
      if (params.sort_by) q.set("sort_by", params.sort_by);
      if (params.order) q.set("order", params.order);

      return fetchWithAuth<any>(`/api/data/sales?${q.toString()}`);
    },

    getCatalog: async (): Promise<any> => {
      return fetchWithAuth<any>("/api/data/catalog");
    },
  },
};
