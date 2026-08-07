"""
ApexMart Retail Ltd. — Sales Performance Dashboard
Dashboard 2 of 5 | Audience: Sales & Merchandising Leadership
"""

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from utils.data_loader import load_all, format_naira
from utils.filters import render_nav, render_global_filters, render_persistent_multiselect
from utils.styling import inject_base_css, kpi_card, NAVY, ACCENT, PLOTLY_TEMPLATE, CATEGORY_COLORS

st.set_page_config(page_title="ApexMart | Sales Performance", page_icon="", layout="wide")
inject_base_css()

st.title("Sales Performance")
st.caption("Category, product, and regional sales performance.")
render_nav("Sales Performance")

data = load_all()
sales_all = data["sales"]
sales = render_global_filters(sales_all)

if sales.empty:
    st.warning("No transactions match the current filters. Adjust the Date Range or Region in the sidebar.")
    st.stop()

# Page-specific filter: Category
st.sidebar.header("Sales Filters")
all_categories = sorted(sales["Category"].dropna().unique().tolist())
selected_categories = render_persistent_multiselect("Category", all_categories, "sales_category_filter")
if selected_categories:
    sales = sales[sales["Category"].isin(selected_categories)]

# ---------------------------------------------------------------------------
# KPI ROW
# ---------------------------------------------------------------------------
c1, c2, c3, c4 = st.columns(4)
with c1:
    kpi_card("Total Revenue", format_naira(sales["Sales_Amount"].sum()))
with c2:
    kpi_card("Total Units Sold", f"{sales['Quantity_Sold'].sum():,.0f}")
with c3:
    kpi_card("Transactions", f"{sales['Transaction_ID'].nunique():,}")
with c4:
    kpi_card("Avg. Basket Value", format_naira(sales["Sales_Amount"].mean()))

st.write("")

# ---------------------------------------------------------------------------
# SALES TREND WITH DECEMBER SEASONALITY BAND
# ---------------------------------------------------------------------------
st.subheader("Sales Trend")
monthly = sales.set_index("Transaction_Date").resample("MS")["Sales_Amount"].sum().reset_index()
fig = go.Figure()
fig.add_trace(go.Scatter(x=monthly["Transaction_Date"], y=monthly["Sales_Amount"],
                          mode="lines+markers", line=dict(color=NAVY, width=3), name="Revenue"))
for year in monthly["Transaction_Date"].dt.year.unique():
    fig.add_vrect(x0=f"{year}-12-01", x1=f"{year}-12-31", fillcolor=ACCENT, opacity=0.12, line_width=0,
                  annotation_text="Festive Season", annotation_position="top left", annotation_font_size=10)
fig.update_layout(template=PLOTLY_TEMPLATE, height=380, margin=dict(l=10, r=10, t=10, b=10))
fig.update_yaxes(title="NGN")
st.plotly_chart(fig, use_container_width=True)

# ---------------------------------------------------------------------------
# TOP PRODUCTS + CATEGORY REVENUE vs PROFIT SHARE
# ---------------------------------------------------------------------------
left, right = st.columns([1.1, 1])

with left:
    st.subheader("Top 15 Products by Revenue")
    top_products = (
        sales.groupby("Product_Name")
        .agg(Revenue=("Sales_Amount", "sum"), Units=("Quantity_Sold", "sum"))
        .reset_index()
        .sort_values("Revenue", ascending=False)
        .head(15)
    )
    fig_top = px.bar(
        top_products.sort_values("Revenue"), x="Revenue", y="Product_Name", orientation="h",
        color="Revenue", color_continuous_scale="Blues",
        labels={"Revenue": "Revenue (NGN)", "Product_Name": ""},
    )
    fig_top.update_layout(template=PLOTLY_TEMPLATE, height=460, margin=dict(l=10, r=10, t=10, b=10),
                           coloraxis_showscale=False)
    st.plotly_chart(fig_top, use_container_width=True)

with right:
    st.subheader("Revenue Share vs. Profit Share by Category")
    cat = sales.groupby("Category").agg(Revenue=("Sales_Amount", "sum"), Profit=("Profit", "sum")).reset_index()
    cat["Rev_Share"] = 100 * cat["Revenue"] / cat["Revenue"].sum()
    cat["Profit_Share"] = 100 * cat["Profit"] / cat["Profit"].sum()
    fig_cat = go.Figure()
    fig_cat.add_trace(go.Bar(x=cat["Category"], y=cat["Rev_Share"], name="Revenue Share %", marker_color=NAVY))
    fig_cat.add_trace(go.Bar(x=cat["Category"], y=cat["Profit_Share"], name="Profit Share %", marker_color=ACCENT))
    fig_cat.update_layout(template=PLOTLY_TEMPLATE, barmode="group", height=460,
                           margin=dict(l=10, r=10, t=10, b=10), legend=dict(orientation="h", y=1.12))
    st.plotly_chart(fig_cat, use_container_width=True)
    st.caption("Where the orange (profit) bar sits below the navy (revenue) bar, the category is diluting margin — a direct signal for pricing/discount review.")

# ---------------------------------------------------------------------------
# REGIONAL SALES BY STORE SIZE
# ---------------------------------------------------------------------------
st.subheader("Regional Sales by Store Size")
region_size = sales.groupby(["Region", "Store_Size"])["Sales_Amount"].sum().reset_index()
fig_region = px.bar(
    region_size, x="Region", y="Sales_Amount", color="Store_Size", barmode="group",
    color_discrete_sequence=CATEGORY_COLORS, labels={"Sales_Amount": "Revenue (NGN)"},
)
fig_region.update_layout(template=PLOTLY_TEMPLATE, height=400, margin=dict(l=10, r=10, t=10, b=10))
st.plotly_chart(fig_region, use_container_width=True)
