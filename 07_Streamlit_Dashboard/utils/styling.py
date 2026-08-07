"""Shared visual styling helpers used across all five dashboard pages."""

from typing import Optional

import streamlit as st

NAVY = "#1F4E79"
ACCENT = "#E07B39"
GREEN = "#2E7D32"
RED = "#C0392B"
GRAY = "#6B7280"

PLOTLY_TEMPLATE = "plotly_white"
CATEGORY_COLORS = ["#1F4E79", "#E07B39", "#2E7D32", "#8E44AD", "#C0392B"]


def inject_base_css():
    st.markdown(
        f"""
        <style>
        .kpi-card {{
            background-color: #F7F8FC;
            border: 1px solid #DCE3F0;
            border-radius: 10px;
            padding: 14px 16px;
            text-align: center;
        }}
        .kpi-value {{
            font-size: 26px;
            font-weight: 700;
            color: {NAVY};
            margin: 0;
        }}
        .kpi-label {{
            font-size: 13px;
            color: {GRAY};
            margin: 0;
        }}
        .kpi-delta-pos {{ color: {GREEN}; font-size: 13px; font-weight: 600; }}
        .kpi-delta-neg {{ color: {RED}; font-size: 13px; font-weight: 600; }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def kpi_card(label: str, value: str, delta: Optional[float] = None, delta_suffix: str = "vs. prior period"):
    delta_html = ""
    if delta is not None and delta == delta:  # not NaN
        cls = "kpi-delta-pos" if delta >= 0 else "kpi-delta-neg"
        arrow = "▲" if delta >= 0 else "▼"
        delta_html = f'<div class="{cls}">{arrow} {abs(delta):.1f}% {delta_suffix}</div>'
    st.markdown(
        f"""
        <div class="kpi-card">
            <p class="kpi-value">{value}</p>
            <p class="kpi-label">{label}</p>
            {delta_html}
        </div>
        """,
        unsafe_allow_html=True,
    )
