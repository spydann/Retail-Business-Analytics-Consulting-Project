"""
Shared sidebar filters and cross-dashboard navigation for the ApexMart
Streamlit dashboard suite.

Every page calls `render_global_filters()` so that the Date Range and
Region selections a user makes on one dashboard are still in effect when
they click through to another — this is what "links" the five dashboards
together into a single coherent analytics experience rather than five
disconnected scripts. Each page then layers its own page-specific filters
(category, store, segment, etc.) on top of this shared base.
"""

import streamlit as st

GLOBAL_DATE_RANGE_KEY = "apexmart_global_date_range"
GLOBAL_REGION_FILTER_KEY = "apexmart_global_region_filter"

PAGES = [
    {"path": "Home.py", "label": "Executive Performance", "icon": ""},
    {"path": "pages/1_Sales_Performance.py", "label": "Sales Performance", "icon": ""},
    {"path": "pages/2_Store_Performance.py", "label": "Store Performance", "icon": ""},
    {"path": "pages/3_Customer_Intelligence.py", "label": "Customer Intelligence", "icon": ""},
    {"path": "pages/4_Inventory_Optimization.py", "label": "Inventory Optimization", "icon": ""},
]


def render_nav(current_label: str):
    """Top-of-page row linking all five dashboards, plus the automatic
    Streamlit sidebar page list. Having both a header nav strip and the
    native sidebar nav means the dashboards stay reachable and clearly
    linked no matter how a viewer arrives at the app."""
    cols = st.columns(len(PAGES))
    for col, page in zip(cols, PAGES):
        with col:
            if page["label"] == current_label:
                st.markdown(f"<b>{page['label']}</b>",
                    unsafe_allow_html=True,
                )
            else:
                st.page_link(page["path"], label=f"{page['icon']} {page['label']}")
    st.divider()


def render_global_filters(sales_df):
    """Renders the shared Date Range + Region filters in the sidebar and
    returns the filtered sales DataFrame. Selections are stored in
    st.session_state under fixed keys so they persist as a user navigates
    between dashboards."""
    st.sidebar.header("Global Filters")
    st.sidebar.caption("Applied across all five dashboards")

    min_date = sales_df["Transaction_Date"].min().date()
    max_date = sales_df["Transaction_Date"].max().date()
    all_regions = sorted(sales_df["Region"].dropna().unique().tolist())

    if GLOBAL_DATE_RANGE_KEY not in st.session_state:
        st.session_state[GLOBAL_DATE_RANGE_KEY] = (min_date, max_date)
    if GLOBAL_REGION_FILTER_KEY not in st.session_state:
        st.session_state[GLOBAL_REGION_FILTER_KEY] = all_regions.copy()

    # NOTE: when a widget's key is already seeded in st.session_state, we
    # deliberately do NOT also pass `value=`/`default=` — Streamlit raises
    # an exception if a widget's default is set both ways in the same run.
    if "date_range" not in st.session_state:
        st.session_state["date_range"] = st.session_state[GLOBAL_DATE_RANGE_KEY]

    date_range = st.sidebar.date_input(
        "Date Range",
        min_value=min_date,
        max_value=max_date,
        key="date_range",
    )
    # date_input can briefly return a single date while the user is
    # mid-selection; guard against that before unpacking.
    if isinstance(date_range, (tuple, list)) and len(date_range) == 2:
        start_date, end_date = date_range
    else:
        start_date, end_date = min_date, max_date
    st.session_state[GLOBAL_DATE_RANGE_KEY] = (start_date, end_date)

    if "region_filter" not in st.session_state:
        st.session_state["region_filter"] = st.session_state[GLOBAL_REGION_FILTER_KEY].copy()

    selected_regions = st.sidebar.multiselect(
        "Region",
        options=all_regions,
        key="region_filter",
    )
    # (default is intentionally omitted — see NOTE above; session_state is
    # pre-seeded with every region selected the first time this renders)
    if not selected_regions:
        selected_regions = all_regions
    st.session_state[GLOBAL_REGION_FILTER_KEY] = list(selected_regions)

    filtered = sales_df[
        (sales_df["Transaction_Date"].dt.date >= start_date)
        & (sales_df["Transaction_Date"].dt.date <= end_date)
        & (sales_df["Region"].isin(selected_regions))
    ]

    st.sidebar.caption(
        f"{len(filtered):,} transactions in current view "
        f"({start_date.isoformat()} → {end_date.isoformat()})"
    )
    st.sidebar.divider()
    return filtered


def render_persistent_multiselect(label: str, options, key: str):
    """Render a sidebar multiselect that survives page navigation.

    The selected values are stored in session_state and pruned to the
    current option list so the widget does not break when upstream filters
    change the available choices.
    """
    options = list(options)
    current = st.session_state.get(key)

    if current is None:
        st.session_state[key] = options.copy()
    else:
        retained = [value for value in current if value in options]
        st.session_state[key] = retained if retained else options.copy()

    selected = st.sidebar.multiselect(label, options=options, key=key)
    if not selected:
        selected = options
        st.session_state[key] = options.copy()

    return selected
