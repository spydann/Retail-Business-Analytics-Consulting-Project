"""
Shared data-loading utilities for the ApexMart Streamlit dashboard suite.

All five dashboard pages import from this module so that every page reads
the same reconciled dataset (data/sales_clean.csv, produced by the data
reconciliation pipeline in 02_SQL and Notebook 2 of 03_Python_Analysis) and
performs identical joins — this is what keeps the five dashboards
consistent with each other and with the numbers quoted in the written
Business Consulting Report.
"""

from pathlib import Path

import numpy as np
import pandas as pd
import streamlit as st

DATA_DIR = Path(__file__).resolve().parent.parent / "data"

# Approximate lat/lon centroids for the Nigerian cities in stores.csv,
# used to plot the regional map on the Executive Dashboard.
CITY_COORDS = {
    "Lagos Island": (6.4541, 3.3947),
    "Ikeja": (6.6018, 3.3515),
    "Lekki": (6.4698, 3.5852),
    "Surulere": (6.5059, 3.3559),
    "Ajah": (6.4667, 3.6000),
    "Ibadan": (7.3775, 3.9470),
    "Abeokuta": (7.1475, 3.3619),
    "Akure": (7.2571, 5.2058),
    "Port Harcourt": (4.8156, 7.0498),
    "Warri": (5.5160, 5.7500),
    "Uyo": (5.0377, 7.9128),
    "Abuja": (9.0765, 7.3986),
    "Jos": (9.8965, 8.8583),
    "Ilorin": (8.4966, 4.5426),
    "Enugu": (6.5244, 7.5086),
    "Onitsha": (6.1667, 6.7833),
    "Aba": (5.1066, 7.3667),
}


@st.cache_data(show_spinner="Loading ApexMart datasets...")
def load_all():
    """Load and join every dataset needed across the five dashboards.

    Returns a dict of DataFrames: sales (fully joined, analysis-ready),
    customers, products, stores, inventory, campaigns, returns, suppliers.
    """
    sales = pd.read_csv(DATA_DIR / "sales_clean.csv", parse_dates=["Transaction_Date"])
    customers = pd.read_csv(DATA_DIR / "customers.csv", parse_dates=["Customer_Since"])
    products = pd.read_csv(DATA_DIR / "products.csv")
    stores = pd.read_csv(DATA_DIR / "stores.csv", parse_dates=["Opening_Date"])
    inventory = pd.read_csv(DATA_DIR / "inventory.csv", parse_dates=["Last_Restock_Date"])
    campaigns = pd.read_csv(DATA_DIR / "marketing_campaigns.csv")
    returns = pd.read_csv(DATA_DIR / "returns.csv", parse_dates=["Return_Date"])
    suppliers = pd.read_csv(DATA_DIR / "suppliers.csv")

    # sales_clean.csv is already reconciled (deduplicated, revenue corrected,
    # missing payments imputed, unmapped store/product rows removed) —
    # see 02_SQL/03_reconciliation.sql and Notebook 2.
    sales = sales.merge(
        products[["Product_ID", "Product_Name", "Category", "Sub_Category"]],
        on="Product_ID", how="left",
    )
    sales = sales.merge(
        stores[["Store_ID", "Store_Name", "Region", "City", "Store_Size",
                 "Number_of_Employees", "Opening_Date"]],
        on="Store_ID", how="left",
    )
    sales = sales.merge(
        customers[["Customer_ID", "Customer_Segment", "Age_Group", "Gender",
                    "Customer_Value_Category", "Customer_Since"]],
        on="Customer_ID", how="left",
    )

    sales["Customer_Segment"] = sales["Customer_Segment"].fillna("Unmapped")
    sales["Region"] = sales["Region"].fillna("Unmapped")
    sales["Lat"] = sales["City"].map(lambda c: CITY_COORDS.get(c, (np.nan, np.nan))[0])
    sales["Lon"] = sales["City"].map(lambda c: CITY_COORDS.get(c, (np.nan, np.nan))[1])

    stores["Lat"] = stores["City"].map(lambda c: CITY_COORDS.get(c, (np.nan, np.nan))[0])
    stores["Lon"] = stores["City"].map(lambda c: CITY_COORDS.get(c, (np.nan, np.nan))[1])
    stores["Tenure_Years"] = (pd.Timestamp("2026-01-01") - stores["Opening_Date"]).dt.days / 365.25

    return {
        "sales": sales,
        "customers": customers,
        "products": products,
        "stores": stores,
        "inventory": inventory,
        "campaigns": campaigns,
        "returns": returns,
        "suppliers": suppliers,
    }


def kpi_delta(current: float, previous: float) -> float:
    """Percent change helper used by every KPI card across the dashboards."""
    if previous in (0, None) or pd.isna(previous):
        return np.nan
    return 100.0 * (current - previous) / previous


def format_naira(value: float) -> str:
    """Consistent NGN formatting used across all five dashboards."""
    if pd.isna(value):
        return "NGN --"
    if abs(value) >= 1_000_000_000:
        return f"NGN {value / 1_000_000_000:,.2f}B"
    if abs(value) >= 1_000_000:
        return f"NGN {value / 1_000_000:,.1f}M"
    if abs(value) >= 1_000:
        return f"NGN {value / 1_000:,.0f}K"
    return f"NGN {value:,.0f}"
