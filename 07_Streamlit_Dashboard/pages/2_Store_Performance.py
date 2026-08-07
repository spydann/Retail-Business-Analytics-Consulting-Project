"""
ApexMart Retail Ltd. — Store Performance Dashboard
Dashboard 3 of 5 | Audience: Regional / Store Operations Leadership
"""

import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st

from utils.data_loader import load_all, format_naira
from utils.filters import render_nav, render_global_filters, render_persistent_multiselect
from utils.styling import inject_base_css, kpi_card, NAVY, ACCENT, PLOTLY_TEMPLATE

st.set_page_config(page_title="ApexMart | Store Performance", page_icon="", layout="wide")
inject_base_css()

st.title("Store Performance")
st.caption("Branch benchmarking, profitability quadrants, and operational productivity.")
render_nav("Store Performance")

data = load_all()
sales_all = data["sales"]
stores = data["stores"]
sales = render_global_filters(sales_all)

if sales.empty:
    st.warning("No transactions match the current filters. Adjust the Date Range or Region in the sidebar.")
    st.stop()

st.sidebar.header("Store Filters")
all_sizes = sorted(sales["Store_Size"].dropna().unique().tolist())
selected_sizes = render_persistent_multiselect("Store Size", all_sizes, "store_size_filter")
if selected_sizes:
    sales = sales[sales["Store_Size"].isin(selected_sizes)]

# ---------------------------------------------------------------------------
# STORE-LEVEL AGGREGATION
# ---------------------------------------------------------------------------
store_perf = (
    sales.groupby(["Store_ID", "Store_Name", "Region", "Store_Size", "Number_of_Employees"])
    .agg(Revenue=("Sales_Amount", "sum"), Profit=("Profit", "sum"))
    .reset_index()
)
store_perf["Margin_Pct"] = 100 * store_perf["Profit"] / store_perf["Revenue"]
store_perf["Revenue_Per_Employee"] = store_perf["Revenue"] / store_perf["Number_of_Employees"]
store_perf = store_perf.merge(stores[["Store_ID", "Tenure_Years"]], on="Store_ID", how="left")

c1, c2, c3, c4 = st.columns(4)
with c1:
    kpi_card("Branches in View", f"{store_perf['Store_ID'].nunique():,}")
with c2:
    kpi_card("Avg. Store Margin %", f"{store_perf['Margin_Pct'].mean():,.1f}%")
with c3:
    top_store = store_perf.sort_values("Revenue", ascending=False).iloc[0]
    kpi_card("Top Store by Revenue", top_store["Store_Name"])
with c4:
    kpi_card("Avg. Revenue / Employee", format_naira(store_perf["Revenue_Per_Employee"].mean()))

st.write("")

# ---------------------------------------------------------------------------
# REVENUE vs MARGIN QUADRANT SCATTER
# ---------------------------------------------------------------------------
st.subheader("Store Revenue vs. Margin — Quadrant View")
avg_rev = store_perf["Revenue"].mean()
avg_margin = store_perf["Margin_Pct"].mean()

fig = px.scatter(
    store_perf, x="Revenue", y="Margin_Pct", size="Revenue", color="Region",
    hover_name="Store_Name", size_max=32,
    labels={"Revenue": "Revenue (NGN)", "Margin_Pct": "Gross Margin %"},
)
fig.add_hline(y=avg_margin, line_dash="dash", line_color="gray")
fig.add_vline(x=avg_rev, line_dash="dash", line_color="gray")
fig.add_annotation(x=store_perf["Revenue"].max(), y=store_perf["Margin_Pct"].min(),
                    text="High Revenue / Low Margin — review discounting", showarrow=False,
                    font=dict(size=11, color=ACCENT), xanchor="right", yanchor="bottom")
fig.update_layout(template=PLOTLY_TEMPLATE, height=460, margin=dict(l=10, r=10, t=10, b=10))
st.plotly_chart(fig, use_container_width=True)

flagged = store_perf[(store_perf["Revenue"] > avg_rev) & (store_perf["Margin_Pct"] < avg_margin)]
if not flagged.empty:
    st.warning(
        f"**{len(flagged)} branch(es)** flagged as high-revenue / below-average-margin: "
        + ", ".join(flagged["Store_Name"].tolist())
    )

# ---------------------------------------------------------------------------
# STORE RANKING TABLE + REVENUE PER EMPLOYEE
# ---------------------------------------------------------------------------
left, right = st.columns([1.2, 1])

with left:
    st.subheader("Store Ranking")
    ranked = store_perf.sort_values("Revenue", ascending=False)[
        ["Store_Name", "Region", "Store_Size", "Revenue", "Profit", "Margin_Pct"]
    ]
    st.dataframe(
        ranked.style.format({"Revenue": "NGN {:,.0f}", "Profit": "NGN {:,.0f}", "Margin_Pct": "{:.1f}%"})
        .background_gradient(subset=["Margin_Pct"], cmap="RdYlGn"),
        use_container_width=True, height=420,
    )

with right:
    st.subheader("Revenue per Employee")
    emp = store_perf.sort_values("Revenue_Per_Employee", ascending=True).tail(15)
    fig_emp = px.bar(
        emp, x="Revenue_Per_Employee", y="Store_Name", orientation="h",
        color="Revenue_Per_Employee", color_continuous_scale="Tealgrn",
        labels={"Revenue_Per_Employee": "Revenue per Employee (NGN)", "Store_Name": ""},
    )
    fig_emp.update_layout(template=PLOTLY_TEMPLATE, height=420, margin=dict(l=10, r=10, t=10, b=10),
                           coloraxis_showscale=False)
    st.plotly_chart(fig_emp, use_container_width=True)

# ---------------------------------------------------------------------------
# STORE MATURITY vs PERFORMANCE
# ---------------------------------------------------------------------------
st.subheader("Store Maturity vs. Revenue")
fig_tenure = px.scatter(
    store_perf, x="Tenure_Years", y="Revenue", color="Store_Size", size="Revenue", size_max=28,
    hover_name="Store_Name",
    labels={"Tenure_Years": "Store Age (Years)", "Revenue": "Revenue (NGN)"},
)
fig_tenure.update_layout(template=PLOTLY_TEMPLATE, height=400, margin=dict(l=10, r=10, t=10, b=10))
st.plotly_chart(fig_tenure, use_container_width=True)
st.caption("Newer branches naturally trail on cumulative revenue — benchmark stores against peers of similar tenure, not the network average.")
