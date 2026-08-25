import pandas as pd
import numpy as np
from datetime import datetime, timedelta

np.random.seed(42)
start_date = datetime(2026, 4, 1)
dates = [start_date + timedelta(days=i) for i in range(91)]  # 91 days: April 1 to June 30

# Product definitions with standard INR retail pricing:
# SKU-KEYBOARD: Rs 4,499.00
# SKU-MONITOR: Rs 24,999.00
products = [
    {"sku": "SKU-KEYBOARD", "base_units": 20, "price": 4499.00, "noise": 4},
    {"sku": "SKU-MONITOR", "base_units": 9, "price": 24999.00, "noise": 2.5}
]
stores = [1, 2]

rows = []
for d in dates:
    date_str = d.strftime("%Y-%m-%d")
    day_of_week = d.weekday()  # 0=Monday, 6=Sunday
    is_weekend = 1.35 if day_of_week in [4, 5, 6] else 1.0  # Fri/Sat/Sun retail lift
    
    # Month-end salary shopping surge (26th to end of month)
    month_end_boost = 1.25 if d.day >= 26 else 1.0
    
    # Summer Mega Sale Event (May 10 to May 15)
    promo_boost = 1.6 if d.month == 5 and 10 <= d.day <= 15 else 1.0
    
    for s in stores:
        store_mult = 1.15 if s == 1 else 0.85  # Store 1 Flagship vs Store 2 Hub
        for p in products:
            mean_demand = p["base_units"] * is_weekend * month_end_boost * promo_boost * store_mult
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
df.to_csv("detailed_sales_data_inr.csv", index=False)
df.to_csv("sample_sales_data_inr.csv", index=False)
print(f"Generated {len(df)} records from {df['date'].min()} to {df['date'].max()}")
print(f"Total Gross Revenue: INR Rs {df['revenue'].sum():,.2f}")
print("Head preview:")
print(df.head(10))
