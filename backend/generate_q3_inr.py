import pandas as pd
import numpy as np
from datetime import datetime, timedelta

np.random.seed(42)

# July 1, 2026 to September 30, 2026 (92 days - Q3)
start_date = datetime(2026, 7, 1)
dates = [start_date + timedelta(days=i) for i in range(92)]

products = [
    {"sku": "SKU-KEYBOARD", "base_units": 22, "price": 4499.00, "noise": 4},
    {"sku": "SKU-MONITOR", "base_units": 10, "price": 24999.00, "noise": 2.5}
]
stores = [1, 2]

rows = []
for d in dates:
    date_str = d.strftime("%Y-%m-%d")
    day_of_week = d.weekday()  # 0=Monday, 6=Sunday
    is_weekend = 1.35 if day_of_week in [4, 5, 6] else 1.0  # Fri/Sat/Sun retail lift
    
    # Month-end salary shopping surge (26th to end of month)
    month_end_boost = 1.25 if d.day >= 26 else 1.0
    
    # Festive Independence Day / Tech Week Sale (Aug 12 to Aug 18)
    festival_boost = 1.65 if d.month == 8 and 12 <= d.day <= 18 else 1.0
    
    for s in stores:
        store_mult = 1.15 if s == 1 else 0.85  # Store 1 Flagship vs Store 2 Hub
        for p in products:
            mean_demand = p["base_units"] * is_weekend * month_end_boost * festival_boost * store_mult
            units = max(1, int(round(np.random.normal(mean_demand, p["noise"]))))
            rev = round(units * p["price"], 2)
            rows.append({
                "date": date_str,
                "sku_code": p["sku"],
                "store_id": s,
                "units_sold": units,
                "revenue": rev
            })

df = pd.DataFrame(rows)
df.to_csv("fresh_sales_data_q3_inr.csv", index=False)
df.to_csv("sample_sales_data_inr.csv", index=False)
print(f"Generated {len(df)} brand new records from {df['date'].min()} to {df['date'].max()}")
print(f"Total Gross Revenue: INR Rs {df['revenue'].sum():,.2f}")
