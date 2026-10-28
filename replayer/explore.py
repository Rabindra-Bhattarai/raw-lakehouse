import pandas as pd

DATA_DIR = "data/olist"
orders = pd.read_csv(f"{DATA_DIR}/olist_orders_dataset.csv", dtype=str)
print("shape:", orders.shape)
print()
print(orders.iloc[0])
print()
print(orders["order_status"].value_counts())
print()
print(orders.isna().sum())
