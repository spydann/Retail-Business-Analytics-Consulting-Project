# Data Dictionary — ApexMart Retail Ltd. Analytics Datasets

## 1. sales_transactions.csv

| Field | Description | Data Type | Example | Business Meaning |
|---|---|---|---|---|
| Transaction_ID | Unique identifier for a POS sales transaction | Text (VARCHAR) | TXN000123 | Primary key; one row = one line-item sale |
| Transaction_Date | Date the sale occurred | Date | 2025-03-14 | Drives all time-series and seasonality analysis |
| Customer_ID | Identifier of the purchasing customer | Text (FK) | C01432 | Links sale to customer profile for segmentation |
| Product_ID | Identifier of the product sold | Text (FK) | P0027 | Links sale to product catalog for margin analysis |
| Store_ID | Identifier of the selling branch | Text (FK) | ST007 | Links sale to branch for regional/store performance |
| Quantity_Sold | Number of units sold in the line item | Integer | 3 | Basket-size and volume driver |
| Unit_Price | Selling price per unit at time of sale | Decimal | 4500.00 | Used to validate Sales_Amount |
| Discount | Naira value of discount applied | Decimal | 250.00 | Feeds discount-vs-margin analysis (Section 6, B5) |
| Sales_Amount | Net amount charged to the customer | Decimal (nullable) | 13250.00 | Core revenue metric; nulls indicate a missing-payment DQ issue |
| Cost_Amount | Total cost of goods for the line item | Decimal | 9000.00 | Basis for profit and margin calculations |
| Profit | Sales_Amount minus Cost_Amount | Decimal | 4250.00 | Primary profitability metric |

## 2. customers.csv

| Field | Description | Data Type | Example | Business Meaning |
|---|---|---|---|---|
| Customer_ID | Unique customer identifier | Text | C01432 | Primary key |
| Customer_Name | Full name of the customer | Text | Ifeoma Okafor | Customer identification (loyalty program) |
| Gender | Customer's stated gender | Text | Female | Demographic segmentation input |
| Age_Group | Age bracket of the customer | Text | 25-34 | Demographic segmentation input |
| Customer_Segment | Assigned marketing segment | Text | Premium | Drives targeted marketing and CLV modelling |
| Location | Customer's city of residence | Text | Ikeja | Geographic demand mapping |
| Customer_Since | Date the customer first registered | Date | 2021-06-02 | Tenure / cohort analysis |
| Customer_Value_Category | Business-assigned value tier | Text | High Value | Prioritization for retention programs |

## 3. products.csv

| Field | Description | Data Type | Example | Business Meaning |
|---|---|---|---|---|
| Product_ID | Unique product/SKU identifier | Text | P0027 | Primary key |
| Product_Name | Descriptive product name | Text | Standing Fan 18in | Product identification |
| Category | Top-level merchandise category | Text | Electronics | Category-level profitability rollups |
| Sub_Category | Secondary classification | Text | Home Appliances | Finer-grained assortment analysis |
| Supplier | Supplying vendor identifier | Text (FK) | SUP004 | Links to supplier performance |
| Cost_Price | Unit cost paid to the supplier | Decimal | 18500.00 | Margin calculation input |
| Selling_Price | Standard shelf/list price | Decimal | 24500.00 | Margin calculation input |
| Product_Status | Lifecycle state of the SKU | Text | Active | Assortment planning (Active/Discontinued/New) |

## 4. stores.csv

| Field | Description | Data Type | Example | Business Meaning |
|---|---|---|---|---|
| Store_ID | Unique branch identifier | Text | ST007 | Primary key |
| Store_Name | Branch display name | Text | ApexMart Ikeja Plaza | Branch identification |
| Region | Geographic region grouping | Text | Lagos | Regional performance rollups |
| City | City in which the branch operates | Text | Ikeja | Local market analysis |
| Store_Size | Store footprint category | Text | Large | Benchmarking peer group |
| Number_of_Employees | Headcount assigned to the branch | Integer | 34 | Revenue-per-employee productivity metric |
| Opening_Date | Date the branch opened | Date | 2019-08-11 | Store maturity / tenure analysis |

## 5. inventory.csv

| Field | Description | Data Type | Example | Business Meaning |
|---|---|---|---|---|
| Inventory_ID | Unique inventory snapshot record identifier | Text | INV003921 | Primary key |
| Product_ID | Product being tracked | Text (FK) | P0027 | Links to product catalog |
| Store_ID | Branch holding the stock | Text (FK) | ST007 | Links to branch |
| Stock_Level | Current on-hand quantity | Integer | 42 | Stockout / overstock risk metric |
| Reorder_Level | Threshold that should trigger replenishment | Integer | 20 | Replenishment planning |
| Inventory_Cost | Value of on-hand stock at cost | Decimal | 777000.00 | Working-capital tied up in inventory |
| Last_Restock_Date | Date of the most recent stock replenishment | Date | 2025-11-02 | Supply-chain responsiveness indicator |

## 6. marketing_campaigns.csv

| Field | Description | Data Type | Example | Business Meaning |
|---|---|---|---|---|
| Campaign_ID | Unique campaign identifier | Text | CMP004 | Primary key |
| Campaign_Name | Campaign display name | Text | Detty December Promo | Campaign identification |
| Campaign_Type | Marketing channel used | Text | Social Media | Channel-mix effectiveness |
| Campaign_Cost | Total spend on the campaign | Decimal | 3200000.00 | ROI denominator |
| Customers_Reached | Estimated audience reached | Integer | 185000 | Reach efficiency metric |
| Revenue_Generated | Attributed revenue from the campaign | Decimal | 5400000.00 | ROI numerator |
| Conversion_Rate | Reached-to-converted ratio | Decimal | 0.0215 | Campaign effectiveness metric |

## 7. returns.csv

| Field | Description | Data Type | Example | Business Meaning |
|---|---|---|---|---|
| Return_ID | Unique return record identifier | Text | RET00341 | Primary key |
| Transaction_ID | Original sale being returned | Text (FK) | TXN000123 | Links return to originating sale |
| Return_Date | Date the return was processed | Date | 2025-04-02 | Returns-processing lag analysis |
| Return_Reason | Stated reason for the return | Text | Defective Product | Root-cause / quality-control input |
| Refund_Amount | Naira value refunded to the customer | Decimal | 8200.00 | Net-revenue impact of returns |

## 8. suppliers.csv

| Field | Description | Data Type | Example | Business Meaning |
|---|---|---|---|---|
| Supplier_ID | Unique supplier identifier | Text | SUP004 | Primary key |
| Supplier_Name | Vendor company name | Text | Novatech Electronics Supplies | Supplier identification |
| Category | Merchandise category supplied | Text | Electronics | Category-supplier mapping |
| Delivery_Performance | % of orders delivered on time | Decimal | 91.4 | Supply-chain reliability metric |
| Supplier_Rating | Internal quality/relationship rating (0-5) | Decimal | 4.2 | Vendor scorecard input |

---
**Note on data quality:** `sales_transactions.csv` and `returns.csv` intentionally contain
seeded data-quality issues (duplicates, orphaned foreign keys, revenue mismatches, and
nulls) to simulate a real client environment. These are catalogued and resolved in
`05_Reports/Data_Quality_Assessment_Report.docx` and `02_SQL/03_reconciliation.sql`.
