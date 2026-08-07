"""
ApexMart Retail Ltd. — Customer Intelligence Dashboard
Dashboard 4 of 5 | Audience: Marketing & Customer Experience Leadership
"""

import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st

from utils.data_loader import load_all, format_naira
from utils.filters import render_nav, render_global_filters, render_persistent_multiselect
from utils.styling import inject_base_css, kpi_card, PLOTLY_TEMPLATE, CATEGORY_COLORS

st.set_page_config(page_title="ApexMart | Customer Intelligence", page_icon="", layout="wide")
inject_base_css()

st.title("Customer Intelligence")
st.caption("Segmentation, lifetime value, and retention behaviour.")
render_nav("Customer Intelligence")

data = load_all()
sales_all = data["sales"]
customers = data["customers"]
sales = render_global_filters(sales_all)

if sales.empty:
    st.warning("No transactions match the current filters. Adjust the Date Range or Region in the sidebar.")
    st.stop()

st.sidebar.header("Customer Filters")
all_segments = sorted(sales["Customer_Segment"].dropna().unique().tolist())
selected_segments = render_persistent_multiselect("Customer Segment", all_segments, "customer_segment_filter")
if selected_segments:
    sales = sales[sales["Customer_Segment"].isin(selected_segments)]

# ---------------------------------------------------------------------------
# SEGMENT KPI ROW
# ---------------------------------------------------------------------------
clv = sales.groupby("Customer_ID")["Sales_Amount"].sum()
txn_counts = sales.groupby("Customer_ID")["Transaction_ID"].nunique()
repeat_share = 100 * (txn_counts >= 2).mean()
top5_threshold = clv.quantile(0.95)
top5_share = 100 * clv[clv >= top5_threshold].sum() / clv.sum() if clv.sum() else np.nan

c1, c2, c3, c4 = st.columns(4)
with c1:
    kpi_card("Customers in View", f"{sales['Customer_ID'].nunique():,}")
with c2:
    kpi_card("Avg. Lifetime Spend", format_naira(clv.mean()))
with c3:
    kpi_card("Repeat Customer Share", f"{repeat_share:,.1f}%")
with c4:
    kpi_card("Top 5% Revenue Share", f"{top5_share:,.1f}%")

st.write("")

# ---------------------------------------------------------------------------
# SEGMENT PERFORMANCE + CLV DISTRIBUTION
# ---------------------------------------------------------------------------
left, right = st.columns([1, 1.2])

with left:
    st.subheader("Revenue by Customer Segment")
    seg = sales.groupby("Customer_Segment")["Sales_Amount"].sum().reset_index().sort_values("Sales_Amount", ascending=False)
    fig_seg = px.bar(
        seg, x="Customer_Segment", y="Sales_Amount", color="Customer_Segment",
        color_discrete_sequence=CATEGORY_COLORS, labels={"Sales_Amount": "Revenue (NGN)", "Customer_Segment": ""},
    )
    fig_seg.update_layout(template=PLOTLY_TEMPLATE, height=380, margin=dict(l=10, r=10, t=10, b=10), showlegend=False)
    st.plotly_chart(fig_seg, use_container_width=True)

with right:
    st.subheader("Customer Lifetime Spend Distribution")
    capped = clv.clip(upper=clv.quantile(0.99))
    fig_hist = px.histogram(capped, nbins=40, labels={"value": "Lifetime Spend (NGN)"},
                             color_discrete_sequence=["#6A51A3"])
    fig_hist.update_layout(template=PLOTLY_TEMPLATE, height=380, margin=dict(l=10, r=10, t=10, b=10), showlegend=False)
    fig_hist.add_vline(x=top5_threshold, line_dash="dash", line_color="#C0392B",
                        annotation_text="Top 5% threshold", annotation_font_size=10)
    st.plotly_chart(fig_hist, use_container_width=True)

# ---------------------------------------------------------------------------
# RETENTION COHORT HEATMAP
# ---------------------------------------------------------------------------
st.subheader("Retention Cohort — Signup Year × Recent Quarterly Activity")
cust_in_view = customers[customers["Customer_ID"].isin(sales["Customer_ID"])].copy()
cust_in_view["Signup_Year"] = cust_in_view["Customer_Since"].dt.year

max_date = sales["Transaction_Date"].max()
quarter_starts = [max_date - pd.Timedelta(days=90 * i) for i in range(4, 0, -1)]
quarter_labels = [f"Q-{4 - i}" for i in range(4)]

cohort_matrix = []
for year in sorted(cust_in_view["Signup_Year"].dropna().unique()):
    cohort_customers = cust_in_view.loc[cust_in_view["Signup_Year"] == year, "Customer_ID"]
    row = []
    for i in range(4):
        q_start = quarter_starts[i]
        q_end = quarter_starts[i + 1] if i + 1 < len(quarter_starts) else max_date
        active_ids = sales.loc[
            (sales["Transaction_Date"] >= q_start) & (sales["Transaction_Date"] <= q_end), "Customer_ID"
        ].unique()
        active_rate = 100 * cohort_customers.isin(active_ids).mean() if len(cohort_customers) else 0
        row.append(active_rate)
    cohort_matrix.append(row)

if cohort_matrix:
    cohort_df = pd.DataFrame(
        cohort_matrix,
        index=[str(int(y)) for y in sorted(cust_in_view["Signup_Year"].dropna().unique())],
        columns=quarter_labels,
    )
    fig_heat = px.imshow(
        cohort_df, text_auto=".0f", color_continuous_scale="Blues", aspect="auto",
        labels=dict(x="Recent Quarter", y="Signup Year Cohort", color="Active %"),
    )
    fig_heat.update_layout(template=PLOTLY_TEMPLATE, height=360, margin=dict(l=10, r=10, t=10, b=10))
    st.plotly_chart(fig_heat, use_container_width=True)
else:
    st.info("Not enough cohort history in the current filter selection to build a retention heatmap.")

# ---------------------------------------------------------------------------
# REPEAT vs ONE-TIME CUSTOMERS
# ---------------------------------------------------------------------------
st.subheader("Repeat vs. One-Time Customers")
repeat_df = pd.DataFrame({
    "Type": ["Repeat Customers", "One-Time Customers"],
    "Share": [repeat_share, 100 - repeat_share],
})
fig_donut = px.pie(repeat_df, names="Type", values="Share", hole=0.55,
                    color_discrete_sequence=["#2E7D32", "#C0392B"])
fig_donut.update_traces(textinfo="percent+label")
fig_donut.update_layout(height=340, margin=dict(l=10, r=10, t=10, b=10), showlegend=False)
st.plotly_chart(fig_donut, use_container_width=True)
