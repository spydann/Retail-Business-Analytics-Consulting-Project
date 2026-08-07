"""
ApexMart Retail Ltd. — Executive Performance Dashboard
Dashboard 1 of 5 | Audience: CEO and Executive Leadership

Run with:  streamlit run Home.py
"""

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from utils.data_loader import load_all, kpi_delta, format_naira
from utils.filters import render_nav, render_global_filters
from utils.styling import inject_base_css, kpi_card, NAVY, ACCENT, PLOTLY_TEMPLATE, CATEGORY_COLORS

st.set_page_config(
    page_title="ApexMart | Executive Dashboard",
    page_icon="",
    layout="wide",
    initial_sidebar_state="expanded",
)
inject_base_css()

st.title("Executive Performance")
st.caption("Retail Profitability & Performance Optimization Engagement — reconciled data, updated through the latest transaction date in the dataset.")
render_nav("Executive Performance")

data = load_all()
sales_all = data["sales"]

sales = render_global_filters(sales_all)

if sales.empty:
    st.warning("No transactions match the current filters. Adjust the Date Range or Region in the sidebar.")
    st.stop()

# ---------------------------------------------------------------------------
# KPI ROW
# ---------------------------------------------------------------------------
start_date = sales["Transaction_Date"].min()
end_date = sales["Transaction_Date"].max()
period_len = (end_date - start_date).days + 1
prior_start = start_date - pd.Timedelta(days=period_len)
prior_end = start_date - pd.Timedelta(days=1)
prior_period = sales_all[
    (sales_all["Transaction_Date"] >= prior_start) & (sales_all["Transaction_Date"] <= prior_end)
]

total_revenue = sales["Sales_Amount"].sum()
total_profit = sales["Profit"].sum()
margin_pct = 100 * total_profit / total_revenue if total_revenue else np.nan

prior_revenue = prior_period["Sales_Amount"].sum()
prior_profit = prior_period["Profit"].sum()
prior_margin = 100 * prior_profit / prior_revenue if prior_revenue else np.nan

active_customers = sales["Customer_ID"].nunique()
prior_customers = prior_period["Customer_ID"].nunique()

inv = data["inventory"]
units_sold = sales["Quantity_Sold"].sum()
avg_stock = inv["Stock_Level"].mean()
inventory_turnover = units_sold / avg_stock if avg_stock else np.nan

c1, c2, c3, c4, c5, c6 = st.columns(6)
with c1:
    kpi_card("Total Revenue", format_naira(total_revenue), kpi_delta(total_revenue, prior_revenue))
with c2:
    kpi_card("Total Profit", format_naira(total_profit), kpi_delta(total_profit, prior_profit))
with c3:
    kpi_card("Gross Margin %", f"{margin_pct:,.1f}%", kpi_delta(margin_pct, prior_margin))
with c4:
    kpi_card("Sales Growth %", f"{kpi_delta(total_revenue, prior_revenue):,.1f}%" if prior_revenue else "n/a", None)
with c5:
    kpi_card("Inventory Turnover", f"{inventory_turnover:,.2f}x", None)
with c6:
    kpi_card("Active Customers", f"{active_customers:,}", kpi_delta(active_customers, prior_customers))

st.write("")

# ---------------------------------------------------------------------------
# TREND + REGIONAL MAP
# ---------------------------------------------------------------------------
left, right = st.columns([1.3, 1])

with left:
    st.subheader("Revenue & Profit Trend")
    monthly = (
        sales.set_index("Transaction_Date")
        .resample("MS")
        .agg(Revenue=("Sales_Amount", "sum"), Profit=("Profit", "sum"))
        .reset_index()
    )
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=monthly["Transaction_Date"], y=monthly["Revenue"],
                              name="Revenue", mode="lines+markers", line=dict(color=NAVY, width=3)))
    fig.add_trace(go.Scatter(x=monthly["Transaction_Date"], y=monthly["Profit"],
                              name="Profit", mode="lines+markers", line=dict(color=ACCENT, width=3)))
    fig.update_layout(template=PLOTLY_TEMPLATE, height=380, hovermode="x unified",
                       margin=dict(l=10, r=10, t=10, b=10), legend=dict(orientation="h", y=1.1))
    fig.update_yaxes(title="NGN")
    st.plotly_chart(fig, use_container_width=True)

with right:
    st.subheader("Regional Performance Map")
    region_geo = (
        sales.dropna(subset=["Lat", "Lon"])
        .groupby(["Region", "City", "Lat", "Lon"])
        .agg(Revenue=("Sales_Amount", "sum"), Profit=("Profit", "sum"))
        .reset_index()
    )
    region_geo["Margin_Pct"] = 100 * region_geo["Profit"] / region_geo["Revenue"]
    fig_map = px.scatter_mapbox(
        region_geo, lat="Lat", lon="Lon", size="Revenue", color="Margin_Pct",
        color_continuous_scale="RdYlGn", size_max=38, zoom=4.6,
        hover_name="City", hover_data={"Region": True, "Revenue": ":,.0f", "Margin_Pct": ":.1f", "Lat": False, "Lon": False},
        mapbox_style="open-street-map",
    )
    fig_map.update_layout(height=380, margin=dict(l=0, r=0, t=0, b=0),
                           coloraxis_colorbar=dict(title="Margin %"))
    st.plotly_chart(fig_map, use_container_width=True)

# ---------------------------------------------------------------------------
# PROFIT BY CATEGORY + REGION SUMMARY TABLE
# ---------------------------------------------------------------------------
left2, right2 = st.columns([1, 1.3])

with left2:
    st.subheader("Profit Share by Category")
    cat_profit = sales.groupby("Category")["Profit"].sum().reset_index().sort_values("Profit", ascending=False)
    fig_pie = px.pie(cat_profit, names="Category", values="Profit", hole=0.5,
                      color_discrete_sequence=CATEGORY_COLORS)
    fig_pie.update_traces(textinfo="percent+label")
    fig_pie.update_layout(height=360, margin=dict(l=10, r=10, t=10, b=10), showlegend=False)
    st.plotly_chart(fig_pie, use_container_width=True)

with right2:
    st.subheader("Regional Summary")
    region_summary = (
        sales.groupby("Region")
        .agg(Revenue=("Sales_Amount", "sum"), Profit=("Profit", "sum"), Transactions=("Transaction_ID", "count"))
        .reset_index()
    )
    region_summary["Margin_Pct"] = 100 * region_summary["Profit"] / region_summary["Revenue"]
    region_summary = region_summary.sort_values("Revenue", ascending=False)
    st.dataframe(
        region_summary.style.format({
            "Revenue": "NGN {:,.0f}", "Profit": "NGN {:,.0f}",
            "Margin_Pct": "{:.1f}%", "Transactions": "{:,.0f}",
        }).background_gradient(subset=["Margin_Pct"], cmap="RdYlGn"),
        use_container_width=True, height=360,
    )

st.divider()
st.markdown(
    "Use the navigation strip above (or the sidebar) to move into "
    "**Sales**, **Store**, **Customer**, or **Inventory** performance — "
    "your Date Range and Region selections carry over automatically."
)
