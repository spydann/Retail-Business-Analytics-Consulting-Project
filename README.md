# Retail Profitability & Performance Optimization
### A Business Analytics Transformation Engagement for ApexMart Retail Ltd.

> **Portfolio note:** ApexMart Retail Ltd. is a fictional company. All datasets are
> synthetically generated (with deliberately seeded data-quality issues) to
> simulate a real consulting engagement. All financial figures quoted are drawn
> from that synthetic dataset and are explicitly labeled as simulated wherever
> used for business-impact estimates.

---

## Project Overview

This repository is an end-to-end, consulting-style business analytics
engagement built for ApexMart Retail Ltd., a 20-branch retailer operating
across five Nigerian regions. It simulates the full lifecycle of a real
analytics consulting project — from raw, imperfect transactional data through
reconciliation, SQL and Python analysis, BI dashboard design, and an
executive-ready consulting report and CEO presentation.

The project is designed to demonstrate the full skill stack of a Business
Analyst / BI Developer / Analytics Consultant: data engineering fundamentals,
SQL analytics, Python-based statistical analysis, dashboard design, and
strategic business communication.

## Business Problem

ApexMart has grown rapidly through branch expansion, but leadership raised
concerns that:

- Revenue is growing while **profit margin is eroding**
- **Branch performance is not visible** to head office in a timely way
- **Inventory is imbalanced** — simultaneous overstock and stockout risk
- **Customer retention** is uneven with no structured high-value program
- **Reporting is fragmented** across disconnected spreadsheets and systems
- The underlying transactional data itself contains **quality issues** that
  would distort any analysis built on top of it

## Objectives

1. Diagnose the root causes of margin erosion and quantify the recovery opportunity
2. Recover and reconcile unreliable transactional data into a trustworthy analytics foundation
3. Design an enterprise-style data architecture and reporting layer
4. Deliver executive and operational dashboards for sales, profit, customers, stores, and inventory
5. Recommend specific, prioritized strategies to improve profitability and retention

## Data Description

Eight datasets underpin the engagement (`01_Data/`), covering January 2024 –
December 2025:

| Dataset | Rows | Description |
|---|---|---|
| `sales_transactions.csv` | ~45,000 | Core POS fact table (line-item sales) |
| `customers.csv` | 2,500 | Customer profiles and segments |
| `products.csv` | 57 | Product catalog across 5 categories |
| `stores.csv` | 20 | Branch network across 5 regions |
| `inventory.csv` | ~875 | Product x Store stock snapshot |
| `marketing_campaigns.csv` | 12 | Campaign spend, reach, and revenue |
| `returns.csv` | ~1,800 | Return records and refund amounts |
| `suppliers.csv` | 12 | Supplier performance and ratings |

Full field-level documentation is in [`01_Data/data_dictionary.md`](01_Data/data_dictionary.md).
The raw extracts contain **intentionally seeded data-quality issues**
(duplicates, orphaned foreign keys, revenue mismatches, missing payments) to
simulate a real client environment — see
[`05_Reports/Data_Quality_Assessment_Report.docx`](05_Reports/Data_Quality_Assessment_Report.docx)
for the full assessment and resolution.

## Tools Used

- **SQL** (schema design, 34-query analytics library, reconciliation logic)
- **Python** — `pandas`, `numpy`, `matplotlib`, `scikit-learn` (Jupyter notebooks)
- **Streamlit + Plotly** (live, interactive 5-dashboard analytics application)
- **Power BI** (original dashboard design specifications, DAX-ready KPI definitions — superseded by the Streamlit app below as the delivered BI layer)
- **Microsoft Word / PowerPoint** — consulting report and CEO presentation

## Analysis Approach

1. **Data Architecture** — relational schema with enforced referential integrity (`02_SQL/01_schema.sql`)
2. **Data Recovery & Reconciliation** — detection and resolution logic for 7 categories of data-quality issue (`02_SQL/03_reconciliation.sql`, Notebook 2)
3. **Exploratory & Statistical Analysis** — 8 Jupyter notebooks (`03_Python_Analysis/`), each **executed end-to-end** against the reconciled dataset, including a scikit-learn regression model of transaction-level margin drivers
4. **Business Intelligence Design** — 5 linked, interactive dashboards built with Streamlit + Plotly (`07_Streamlit_Dashboard/`)
5. **Consulting Synthesis** — findings translated into root causes, prioritized recommendations, an implementation roadmap, and simulated business impact (`05_Reports/`, `06_Presentation/`)

## Interactive Dashboard Suite

The five dashboards are delivered as a **live, interactive Streamlit + Plotly
application** in [`07_Streamlit_Dashboard/`](07_Streamlit_Dashboard/),
All five dashboards share one reconciled data layer and a persistent set of
global filters (Date Range, Region), and are cross-linked via both a
navigation strip on every page and Streamlit's native sidebar page list:

1. **Executive Performance** (`Home.py`) — KPI strip, revenue/profit trend, regional map, category profit mix
2. **Sales Performance** (`pages/1_Sales_Performance.py`) — sales trend, top products, category revenue vs. profit share
3. **Store Performance** (`pages/2_Store_Performance.py`) — store ranking, revenue-vs-margin quadrant, revenue per employee
4. **Customer Intelligence** (`pages/3_Customer_Intelligence.py`) — segmentation, CLV distribution, retention cohort heatmap
5. **Inventory Optimization** (`pages/4_Inventory_Optimization.py`) — turnover, stock-shortage risk, slow-moving inventory

Run it locally with `cd 07_Streamlit_Dashboard && pip install -r requirements.txt && streamlit run Home.py`,
or deploy it for free on Streamlit Community Cloud — see
[`07_Streamlit_Dashboard/README.md`](07_Streamlit_Dashboard/README.md) for full instructions.

Below are two of the underlying analytical visuals (generated in
`03_Python_Analysis`) that the Executive and Store Performance dashboards are
built from:

![Monthly Revenue & Profit](04_PowerBI_Dashboard/sample_visuals/eda_1.png)
![Store Revenue vs Margin Quadrant](04_PowerBI_Dashboard/sample_visuals/store_1.png)

## Key Findings

| Metric | Value |
|---|---|
| Total revenue analyzed (24 months, reconciled) | NGN 1,011,488,365 |
| Total profit (24 months, reconciled) | NGN 227,168,641 |
| Overall gross margin | 22.5% |
| Margin, first quarter vs. most recent quarter | 23.2% → 20.1% (−3.2 pts) |
| Correlation, discount depth vs. margin | −0.42 |
| Revenue / profit share, Electronics category | 52.7% / 56.1% |
| Top 5% of customers' share of total revenue | 10.1% |
| Inventory value tied up in overstock | NGN 47,950,312 |
| Product-store combinations at/below reorder level | 35% (305 of 874) |

Full findings, root-cause analysis, and category/store/customer breakdowns
are in the [Business Consulting Report](05_Reports/Business_Consulting_Report.docx)
and the analysis notebooks.

## Business Recommendations

1. **Introduce discount-approval thresholds** — cap standard discounts at 20%
2. **Rationalize the bottom-margin product tail** — reprice, renegotiate, or delist
3. **Rebalance inventory across the network** — move to velocity-based replenishment
4. **Standardize branch operating discipline** — close the 4x revenue-per-employee gap
5. **Close the marketing-to-POS attribution gap** — add Campaign_ID to POS transactions
6. **Launch a high-value customer retention program** — target the top 5% of customers
7. **Institutionalize data governance** — automate the reconciliation checks in `02_SQL/`

## Simulated Business Impact

*(All figures below are simulated, directional estimates derived from this
engagement's reconciled dataset — see the Business Consulting Report, Section 7,
for full caveats.)*

- **NGN 16.2 million/year** estimated profitability recovery from closing the observed margin gap via discount governance
- **NGN 8.6 million** estimated working-capital release from an 18% reduction in overstocked inventory
- **305 product-store combinations (35%)** identified as at/below reorder level, an avoidable lost-sale risk once resequenced
- **Zero of 12** marketing campaigns show negative ROI, though this cannot yet be independently verified at the transaction level
- A single, reconciled source of truth to replace fragmented, store-level spreadsheet reporting

---

## Repository Structure

```
Retail-Business-Analytics-Consulting-Project/
├── 01_Data/                      # 8 CSV datasets + data dictionary
├── 02_SQL/                       # Schema, 34-query analytics library, reconciliation logic
├── 03_Python_Analysis/           # 8 executed Jupyter notebooks
├── 04_PowerBI_Dashboard/         # Original dashboard design specs + sample analytical visuals
├── 05_Reports/                   # Data Quality Assessment + Business Consulting Report (Word)
├── 06_Presentation/              # 13-slide CEO presentation (PowerPoint)
├── 07_Streamlit_Dashboard/       # Live interactive 5-dashboard app (Streamlit + Plotly)
└── README.md
```
