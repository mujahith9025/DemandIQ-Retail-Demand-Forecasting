export interface HealthCheckResponse {
  status: 'healthy' | 'degraded' | 'unhealthy';
  service: string;
  version: string;
  environment: string;
  database: string;
  uptime_seconds?: number;
  timestamp: string;
  details?: Record<string, unknown>;
}

export interface User {
  id: number;
  name: string;
  email: string;
  role: 'admin' | 'planner' | 'store_manager';
  assigned_store_id?: number | null;
  created_at?: string;
  updated_at?: string;
}

export interface AuthResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
  user: User;
}

export interface RefreshTokenResponse {
  access_token: string;
  token_type: string;
  expires_in: number;
}

export interface Product {
  id: number;
  sku_code: string;
  name: string;
  category: string;
  subcategory?: string;
  unit_price: number;
  unit_cost: number;
  lead_time_days: number;
  created_at?: string;
  updated_at?: string;
}

export interface Store {
  id: number;
  name: string;
  location: string;
  city: string;
  region: string;
  timezone: string;
}

export interface Promotion {
  id: number;
  name: string;
  discount_pct: number;
  start_date: string;
  end_date: string;
  product_id?: number;
  category?: string;
}

export interface ForecastPredictionItem {
  week_index: number;
  forecast_date: string;
  week_end_date: string;
  predicted_units: number;
  lower_bound: number;
  upper_bound: number;
  confidence_level: number | string;
  is_cold_start: boolean;
  model_used: string;
  product_id: number;
  store_id: number;
}

export interface ForecastPredictionResponse {
  product_id: number;
  store_id: number;
  horizon_weeks: number;
  model_type: string;
  predictions: ForecastPredictionItem[];
}

export interface ForecastAccuracyResponse {
  product_id: number;
  store_id: number;
  is_cold_start: boolean;
  validation_days?: number;
  ensemble_metrics?: { mape: number; rmse: number };
  prophet_metrics?: { mape: number; rmse: number };
  xgboost_metrics?: { mape: number; rmse: number };
  prophet_weight?: number;
  xgboost_weight?: number;
  mape?: number;
  rmse?: number;
  message?: string;
}

export interface ReorderRecommendationItem {
  product_id: number;
  sku_code: string;
  product_name: string;
  category: string;
  store_id: number;
  current_stock: number;
  reorder_point: number;
  safety_stock: number;
  lead_time_days: number;
  suggested_order_qty: number;
  unit_cost: number;
  estimated_order_cost: number;
  risk_level: 'CRITICAL' | 'WARNING' | 'OK';
  days_of_supply_remaining: number;
}

export interface PurchaseOrder {
  id: number;
  product_id: number;
  store_id: number;
  order_quantity: number;
  unit_cost: number;
  total_cost: number;
  status: 'draft' | 'submitted' | 'received' | 'cancelled';
  supplier_name: string;
  expected_delivery_date?: string;
  created_at: string;
}

export interface Alert {
  id: number;
  type: 'spike' | 'drop' | 'stockout';
  severity: 'critical' | 'warning' | 'info';
  product_id?: number;
  store_id?: number;
  message: string;
  status: 'new' | 'acknowledged' | 'dismissed';
  created_at: string;
}

export interface SimulationDayPoint {
  day_index: number;
  date: string;
  baseline_units: number;
  simulated_units: number;
  uplift_pct: number;
  baseline_revenue: number;
  simulated_revenue: number;
}

export interface SimulatePromoResponse {
  product_id?: number;
  category?: string;
  discount_pct: number;
  promo_duration_days: number;
  estimated_elasticity: number;
  total_baseline_units: number;
  total_simulated_units: number;
  total_unit_uplift: number;
  total_unit_uplift_pct: number;
  total_baseline_revenue: number;
  total_simulated_revenue: number;
  total_revenue_impact: number;
  curve: SimulationDayPoint[];
}

export interface ReportItem {
  id: number;
  title: string;
  report_type: string;
  format: string;
  status: string;
  created_at: string;
  summary_metrics?: Record<string, any>;
}

export interface DashboardKPIs {
  store_id?: number | null;
  projected_revenue_30d: number;
  revenue_growth_pct: number;
  overall_accuracy_pct: number;
  accuracy_change_pct: number;
  total_active_products: number;
  total_stores: number;
  stockout_risk_count: number;
  overstock_risk_count: number;
  urgent_reorder_count: number;
  generated_at: string;
  trend_data?: Array<{
    date: string;
    historical_sales: number | null;
    predicted_demand: number;
    lower_bound: number;
    upper_bound: number;
  }>;
  top_skus?: Array<{
    sku: string;
    name: string;
    category: string;
    predicted_30d_units: number;
    growth_pct: number;
  }>;
}

export interface PaginatedResult<T> {
  total: number;
  limit: number;
  offset: number;
  items: T[];
}

export interface RowValidationError {
  row_number: number;
  column?: string;
  issue: string;
  raw_value?: string;
}

export interface DataUploadSuccessResponse {
  status: 'success';
  message: string;
  total_rows: number;
  inserted_rows: number;
  date_range?: {
    start_date: string;
    end_date: string;
  };
  background_job_triggered: boolean;
}

export interface DataUploadErrorResponse {
  status: 'validation_error';
  message: string;
  error_count: number;
  errors: RowValidationError[];
}
