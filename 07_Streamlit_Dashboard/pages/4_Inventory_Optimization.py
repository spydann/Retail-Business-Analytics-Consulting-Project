"""
ApexMart Retail Ltd. — Inventory Optimization Dashboard
Dashboard 5 of 5 | Audience: Supply Chain & Inventory Planning Leadership
"""

import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st

from utils.data_loader import load_all, format_naira
from utils.filters import (
    GLOBAL_REGION_FILTER_KEY,
    render_nav,
    render_global_filters,
    render_persistent_multiselect,
)
from utils.styling import inject_base_css, kpi_card, PLOTLY_TEMPLATE

st.set_page_config(page_title="ApexMart | Inventory Optimization", page_icon="", layout="wide")
inject_base_css()

st.title("Inventory Optimization")
st.caption("Stock efficiency, turnover, and replenishment risk across the store network.")
render_nav("Inventory Optimization")

data = load_all()
sales_all = data["sales"]
inventory = data["inventory"].merge(
    data["products"][["Product_ID", "Product_Name", "Category"]], on="Product_ID", how="left"
).merge(
    data["stores"][["Store_ID", "Store_Name", "Region"]], on="Store_ID", how="left"
)
sales = render_global_filters(sales_all)

if sales.empty:
    st.warning("No transactions match the current filters. Adjust the Date Range or Region in the sidebar.")
    st.stop()

# Keep inventory in sync with the persisted Region filter applied to sales.
selected_regions = st.session_state.get(GLOBAL_REGION_FILTER_KEY) or sorted(inventory["Region"].dropna().unique().tolist())
inventory = inventory[inventory["Region"].isin(selected_regions)]

st.sidebar.header("Inventory Filters")
all_categories = sorted(inventory["Category"].dropna().unique().tolist())
selected_categories = render_persistent_multiselect("Category", all_categories, "inventory_category_filter")
if selected_categories:
    inventory = inventory[inventory["Category"].isin(selected_categories)]

# ---------------------------------------------------------------------------
# KPI ROW
# ---------------------------------------------------------------------------
units_sold_90d = sales[sales["Transaction_Date"] >= sales["Transaction_Date"].max() - pd.Timedelta(days=90)][
    "Quantity_Sold"
].sum()
avg_stock = inventory["Stock_Level"].mean()
turnover_ratio = units_sold_90d / avg_stock if avg_stock else np.nan
total_inv_cost = inventory["Inventory_Cost"].sum()
overstock_mask = inventory["Stock_Level"] > inventory["Reorder_Level"] * 2
reorder_risk_mask = inventory["Stock_Level"] <= inventory["Reorder_Level"]
pct_overstocked = 100 * overstock_mask.mean() if len(inventory) else np.nan
pct_at_risk = 100 * reorder_risk_mask.mean() if len(inventory) else np.nan

c1, c2, c3, c4 = st.columns(4)
with c1:
    kpi_card("Inventory Turnover (90d)", f"{turnover_ratio:,.2f}x")
with c2:
    kpi_card("Total Inventory Cost", format_naira(total_inv_cost))
with c3:
    kpi_card("SKUs at Reorder Risk", f"{pct_at_risk:,.1f}%")
with c4:
    kpi_card("SKUs Overstocked", f"{pct_overstocked:,.1f}%")

st.write("")

# ---------------------------------------------------------------------------
# STOCK RISK TABLE
# ---------------------------------------------------------------------------
left, right = st.columns([1, 1])

with left:
    st.subheader("Stock Shortage Risk (At or Below Reorder Level)")
    shortage = inventory[reorder_risk_mask][
        ["Product_Name", "Store_Name", "Region", "Stock_Level", "Reorder_Level"]
    ].sort_values("Stock_Level")
    st.dataframe(
        shortage.style.format({"Stock_Level": "{:,.0f}", "Reorder_Level": "{:,.0f}"})
        .background_gradient(subset=["Stock_Level"], cmap="Reds_r"),
        use_container_width=True, height=380,
    )
    st.caption(f"{len(shortage):,} product-store combinations currently at or below their reorder threshold.")

with right:
    st.subheader("Slow-Moving Inventory (Overstocked, Low Recent Sales)")
    recent_sales = sales[sales["Transaction_Date"] >= sales["Transaction_Date"].max() - pd.Timedelta(days=90)]
    velocity = recent_sales.groupby(["Product_ID", "Store_ID"])["Quantity_Sold"].sum().reset_index()
    velocity.columns = ["Product_ID", "Store_ID", "Units_Sold_90d"]
    slow_moving = inventory.merge(velocity, on=["Product_ID", "Store_ID"], how="left")
    slow_moving["Units_Sold_90d"] = slow_moving["Units_Sold_90d"].fillna(0)
    slow_moving = slow_moving[
        (slow_moving["Stock_Level"] > slow_moving["Reorder_Level"] * 2) & (slow_moving["Units_Sold_90d"] < 5)
    ][["Product_Name", "Store_Name", "Stock_Level", "Units_Sold_90d", "Inventory_Cost"]].sort_values(
        "Inventory_Cost", ascending=False
    )
    st.dataframe(
        slow_moving.style.format({
            "Stock_Level": "{:,.0f}", "Units_Sold_90d": "{:,.0f}", "Inventory_Cost": "NGN {:,.0f}",
        }),
        use_container_width=True, height=380,
    )
    st.caption(
        f"{len(slow_moving):,} combinations flagged as slow-moving, "
        f"tying up {format_naira(slow_moving['Inventory_Cost'].sum())} in working capital."
    )

# ---------------------------------------------------------------------------
# INVENTORY COST BY STORE
# ---------------------------------------------------------------------------
st.subheader("Inventory Carrying Cost by Store")
store_cost = inventory.groupby("Store_Name")["Inventory_Cost"].sum().reset_index().sort_values(
    "Inventory_Cost", ascending=True
).tail(20)
fig_cost = px.bar(
    store_cost, x="Inventory_Cost", y="Store_Name", orientation="h",
    color="Inventory_Cost", color_continuous_scale="Oranges",
    labels={"Inventory_Cost": "Inventory Cost (NGN)", "Store_Name": ""},
)
fig_cost.update_layout(template=PLOTLY_TEMPLATE, height=520, margin=dict(l=10, r=10, t=10, b=10),
                        coloraxis_showscale=False)
st.plotly_chart(fig_cost, use_container_width=True)
