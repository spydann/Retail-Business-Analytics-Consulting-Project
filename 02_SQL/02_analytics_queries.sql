/* =============================================================================
   RETAIL_ANALYTICS_DB — BUSINESS ANALYTICS QUERY LIBRARY
   Client: ApexMart Retail Ltd.
   Note: All monetary queries below run against Sales.Sales_Amount, which
   contains known nulls (missing-payment records) and mismatches. Queries
   flagged (RECONCILED) filter to Data_Quality_Flag = 'Clean' — see
   03_reconciliation.sql for how that flag is derived.
   ============================================================================= */

-- =============================================================================
-- A. SALES ANALYSIS
-- =============================================================================

-- A1. Total revenue (all-time, excluding rows with missing payments)
SELECT ROUND(SUM(Sales_Amount), 2) AS Total_Revenue
FROM Sales
WHERE Sales_Amount IS NOT NULL;

-- A2. Monthly sales trend
SELECT DATE_TRUNC('month', Transaction_Date) AS Sales_Month,
       ROUND(SUM(Sales_Amount), 2)            AS Monthly_Revenue,
       COUNT(DISTINCT Transaction_ID)          AS Transaction_Count
FROM Sales
WHERE Sales_Amount IS NOT NULL
GROUP BY 1
ORDER BY 1;

-- A3. Year-over-year monthly comparison
SELECT EXTRACT(MONTH FROM Transaction_Date) AS Month_No,
       EXTRACT(YEAR FROM Transaction_Date)  AS Year,
       ROUND(SUM(Sales_Amount), 2)          AS Revenue
FROM Sales
WHERE Sales_Amount IS NOT NULL
GROUP BY 1, 2
ORDER BY 1, 2;

-- A4. Regional sales performance
SELECT s.Region,
       ROUND(SUM(sl.Sales_Amount), 2) AS Regional_Revenue,
       COUNT(DISTINCT sl.Transaction_ID) AS Transactions
FROM Sales sl
JOIN Stores s ON sl.Store_ID = s.Store_ID
WHERE sl.Sales_Amount IS NOT NULL
GROUP BY s.Region
ORDER BY Regional_Revenue DESC;

-- A5. City-level sales performance
SELECT s.City, ROUND(SUM(sl.Sales_Amount), 2) AS City_Revenue
FROM Sales sl JOIN Stores s ON sl.Store_ID = s.Store_ID
WHERE sl.Sales_Amount IS NOT NULL
GROUP BY s.City
ORDER BY City_Revenue DESC;

-- A6. Product sales ranking (top 20 by revenue)
SELECT p.Product_Name, p.Category,
       ROUND(SUM(sl.Sales_Amount), 2) AS Product_Revenue,
       SUM(sl.Quantity_Sold)           AS Units_Sold
FROM Sales sl JOIN Products p ON sl.Product_ID = p.Product_ID
WHERE sl.Sales_Amount IS NOT NULL
GROUP BY p.Product_Name, p.Category
ORDER BY Product_Revenue DESC
LIMIT 20;

-- A7. Category-level revenue contribution (% of total)
SELECT p.Category,
       ROUND(SUM(sl.Sales_Amount), 2) AS Category_Revenue,
       ROUND(100.0 * SUM(sl.Sales_Amount) / SUM(SUM(sl.Sales_Amount)) OVER (), 2) AS Pct_of_Total
FROM Sales sl JOIN Products p ON sl.Product_ID = p.Product_ID
WHERE sl.Sales_Amount IS NOT NULL
GROUP BY p.Category
ORDER BY Category_Revenue DESC;

-- A8. Day-of-week sales pattern (staffing / promo timing insight)
SELECT TO_CHAR(Transaction_Date, 'Day') AS Day_Of_Week,
       ROUND(AVG(Sales_Amount), 2)      AS Avg_Transaction_Value,
       COUNT(*)                         AS Transaction_Count
FROM Sales
WHERE Sales_Amount IS NOT NULL
GROUP BY 1
ORDER BY Transaction_Count DESC;

-- A9. Average basket / transaction value trend by month
SELECT DATE_TRUNC('month', Transaction_Date) AS Sales_Month,
       ROUND(AVG(Sales_Amount), 2) AS Avg_Basket_Value
FROM Sales
WHERE Sales_Amount IS NOT NULL
GROUP BY 1
ORDER BY 1;

-- =============================================================================
-- B. PROFITABILITY ANALYSIS
-- =============================================================================

-- B1. Overall gross profit and margin
SELECT ROUND(SUM(Sales_Amount), 2)                       AS Total_Revenue,
       ROUND(SUM(Cost_Amount), 2)                         AS Total_Cost,
       ROUND(SUM(Profit), 2)                              AS Gross_Profit,
       ROUND(100.0 * SUM(Profit) / NULLIF(SUM(Sales_Amount),0), 2) AS Gross_Margin_Pct
FROM Sales
WHERE Sales_Amount IS NOT NULL;

-- B2. Profit margin by product category
SELECT p.Category,
       ROUND(SUM(sl.Sales_Amount), 2) AS Revenue,
       ROUND(SUM(sl.Profit), 2)        AS Profit,
       ROUND(100.0 * SUM(sl.Profit) / NULLIF(SUM(sl.Sales_Amount),0), 2) AS Margin_Pct
FROM Sales sl JOIN Products p ON sl.Product_ID = p.Product_ID
WHERE sl.Sales_Amount IS NOT NULL
GROUP BY p.Category
ORDER BY Margin_Pct ASC;

-- B3. Most profitable products (top 15)
SELECT p.Product_Name, p.Category, ROUND(SUM(sl.Profit), 2) AS Total_Profit
FROM Sales sl JOIN Products p ON sl.Product_ID = p.Product_ID
WHERE sl.Sales_Amount IS NOT NULL
GROUP BY p.Product_Name, p.Category
ORDER BY Total_Profit DESC
LIMIT 15;

-- B4. Least profitable / margin-eroding products (bottom 15)
SELECT p.Product_Name, p.Category,
       ROUND(SUM(sl.Profit), 2) AS Total_Profit,
       ROUND(100.0 * SUM(sl.Profit) / NULLIF(SUM(sl.Sales_Amount),0), 2) AS Margin_Pct
FROM Sales sl JOIN Products p ON sl.Product_ID = p.Product_ID
WHERE sl.Sales_Amount IS NOT NULL
GROUP BY p.Product_Name, p.Category
HAVING SUM(sl.Sales_Amount) > 0
ORDER BY Margin_Pct ASC
LIMIT 15;

-- B5. Discount impact on profitability (correlation view)
SELECT CASE
         WHEN sl.Discount / NULLIF(sl.Unit_Price * sl.Quantity_Sold,0) <= 0.05 THEN '0-5%'
         WHEN sl.Discount / NULLIF(sl.Unit_Price * sl.Quantity_Sold,0) <= 0.15 THEN '5-15%'
         WHEN sl.Discount / NULLIF(sl.Unit_Price * sl.Quantity_Sold,0) <= 0.30 THEN '15-30%'
         ELSE '30%+'
       END AS Discount_Band,
       ROUND(AVG(100.0 * sl.Profit / NULLIF(sl.Sales_Amount,0)), 2) AS Avg_Margin_Pct,
       COUNT(*) AS Transactions
FROM Sales sl
WHERE sl.Sales_Amount IS NOT NULL AND sl.Sales_Amount > 0
GROUP BY 1
ORDER BY 1;

-- B6. Profitability by store region
SELECT s.Region, ROUND(SUM(sl.Profit), 2) AS Profit,
       ROUND(100.0 * SUM(sl.Profit) / NULLIF(SUM(sl.Sales_Amount),0), 2) AS Margin_Pct
FROM Sales sl JOIN Stores s ON sl.Store_ID = s.Store_ID
WHERE sl.Sales_Amount IS NOT NULL
GROUP BY s.Region
ORDER BY Margin_Pct DESC;

-- B7. Monthly gross margin trend (used to spot the margin erosion cited in the exec summary)
SELECT DATE_TRUNC('month', Transaction_Date) AS Sales_Month,
       ROUND(100.0 * SUM(Profit) / NULLIF(SUM(Sales_Amount),0), 2) AS Margin_Pct
FROM Sales
WHERE Sales_Amount IS NOT NULL
GROUP BY 1
ORDER BY 1;

-- =============================================================================
-- C. CUSTOMER ANALYSIS
-- =============================================================================

-- C1. Customer segmentation performance
SELECT c.Customer_Segment,
       COUNT(DISTINCT c.Customer_ID)     AS Customers,
       ROUND(SUM(sl.Sales_Amount), 2)     AS Revenue,
       ROUND(AVG(sl.Sales_Amount), 2)      AS Avg_Transaction_Value
FROM Sales sl JOIN Customers c ON sl.Customer_ID = c.Customer_ID
WHERE sl.Sales_Amount IS NOT NULL
GROUP BY c.Customer_Segment
ORDER BY Revenue DESC;

-- C2. Repeat customers (2+ transactions) vs one-time customers
SELECT CASE WHEN Txn_Count >= 2 THEN 'Repeat Customer' ELSE 'One-Time Customer' END AS Customer_Type,
       COUNT(*) AS Customers
FROM (
    SELECT Customer_ID, COUNT(DISTINCT Transaction_ID) AS Txn_Count
    FROM Sales
    GROUP BY Customer_ID
) t
GROUP BY 1;

-- C3. High-value customers (top 5% by lifetime spend)
WITH customer_spend AS (
    SELECT Customer_ID, SUM(Sales_Amount) AS Lifetime_Spend
    FROM Sales
    WHERE Sales_Amount IS NOT NULL
    GROUP BY Customer_ID
)
SELECT Customer_ID, Lifetime_Spend
FROM customer_spend
WHERE Lifetime_Spend >= (
    SELECT PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY Lifetime_Spend) FROM customer_spend
)
ORDER BY Lifetime_Spend DESC;

-- C4. Customer value category vs actual spend validation
SELECT c.Customer_Value_Category,
       ROUND(AVG(cust_rev.Lifetime_Spend), 2) AS Avg_Actual_Spend
FROM Customers c
JOIN (SELECT Customer_ID, SUM(Sales_Amount) AS Lifetime_Spend
      FROM Sales WHERE Sales_Amount IS NOT NULL GROUP BY Customer_ID) cust_rev
  ON c.Customer_ID = cust_rev.Customer_ID
GROUP BY c.Customer_Value_Category
ORDER BY Avg_Actual_Spend DESC;

-- C5. Customer age-group purchasing behaviour
SELECT c.Age_Group, ROUND(SUM(sl.Sales_Amount), 2) AS Revenue,
       ROUND(AVG(sl.Sales_Amount), 2) AS Avg_Basket
FROM Sales sl JOIN Customers c ON sl.Customer_ID = c.Customer_ID
WHERE sl.Sales_Amount IS NOT NULL
GROUP BY c.Age_Group
ORDER BY Revenue DESC;

-- C6. Customer retention cohort (by signup year, whether they purchased in the latest quarter)
SELECT EXTRACT(YEAR FROM c.Customer_Since) AS Signup_Year,
       COUNT(DISTINCT c.Customer_ID) AS Cohort_Size,
       COUNT(DISTINCT CASE WHEN sl.Transaction_Date >= DATE '2025-10-01' THEN sl.Customer_ID END) AS Active_Last_Quarter
FROM Customers c
LEFT JOIN Sales sl ON c.Customer_ID = sl.Customer_ID
GROUP BY 1
ORDER BY 1;

-- =============================================================================
-- D. STORE / BRANCH ANALYSIS
-- =============================================================================

-- D1. Best performing stores by revenue
SELECT s.Store_Name, s.Region, ROUND(SUM(sl.Sales_Amount), 2) AS Revenue
FROM Sales sl JOIN Stores s ON sl.Store_ID = s.Store_ID
WHERE sl.Sales_Amount IS NOT NULL
GROUP BY s.Store_Name, s.Region
ORDER BY Revenue DESC
LIMIT 10;

-- D2. Worst performing stores by revenue
SELECT s.Store_Name, s.Region, ROUND(SUM(sl.Sales_Amount), 2) AS Revenue
FROM Sales sl JOIN Stores s ON sl.Store_ID = s.Store_ID
WHERE sl.Sales_Amount IS NOT NULL
GROUP BY s.Store_Name, s.Region
ORDER BY Revenue ASC
LIMIT 10;

-- D3. Store profitability comparison (revenue high but margin low = "leaky" branches)
SELECT s.Store_Name,
       ROUND(SUM(sl.Sales_Amount), 2)                                       AS Revenue,
       ROUND(100.0 * SUM(sl.Profit) / NULLIF(SUM(sl.Sales_Amount),0), 2)    AS Margin_Pct
FROM Sales sl JOIN Stores s ON sl.Store_ID = s.Store_ID
WHERE sl.Sales_Amount IS NOT NULL
GROUP BY s.Store_Name
ORDER BY Revenue DESC;

-- D4. Revenue per employee (operational efficiency)
SELECT s.Store_Name, s.Number_of_Employees,
       ROUND(SUM(sl.Sales_Amount), 2)                              AS Revenue,
       ROUND(SUM(sl.Sales_Amount) / s.Number_of_Employees, 2)        AS Revenue_Per_Employee
FROM Sales sl JOIN Stores s ON sl.Store_ID = s.Store_ID
WHERE sl.Sales_Amount IS NOT NULL
GROUP BY s.Store_Name, s.Number_of_Employees
ORDER BY Revenue_Per_Employee DESC;

-- D5. Store performance by size category
SELECT s.Store_Size, ROUND(AVG(store_rev.Revenue), 2) AS Avg_Revenue_Per_Store
FROM Stores s
JOIN (SELECT Store_ID, SUM(Sales_Amount) AS Revenue FROM Sales WHERE Sales_Amount IS NOT NULL GROUP BY Store_ID) store_rev
  ON s.Store_ID = store_rev.Store_ID
GROUP BY s.Store_Size
ORDER BY Avg_Revenue_Per_Store DESC;

-- D6. New vs mature store performance (tenure-adjusted)
SELECT CASE WHEN s.Opening_Date <= DATE '2022-01-01' THEN 'Mature (4+ yrs)' ELSE 'Newer Store' END AS Store_Tenure,
       ROUND(AVG(store_rev.Revenue), 2) AS Avg_Revenue
FROM Stores s
JOIN (SELECT Store_ID, SUM(Sales_Amount) AS Revenue FROM Sales WHERE Sales_Amount IS NOT NULL GROUP BY Store_ID) store_rev
  ON s.Store_ID = store_rev.Store_ID
GROUP BY 1;

-- =============================================================================
-- E. INVENTORY ANALYSIS
-- =============================================================================

-- E1. Slow-moving inventory (high stock, low sales velocity over last 90 days)
SELECT i.Product_ID, p.Product_Name, i.Store_ID, i.Stock_Level,
       COALESCE(sold.Units_Sold_90d, 0) AS Units_Sold_90d
FROM Inventory i
JOIN Products p ON i.Product_ID = p.Product_ID
LEFT JOIN (
    SELECT Product_ID, Store_ID, SUM(Quantity_Sold) AS Units_Sold_90d
    FROM Sales
    WHERE Transaction_Date >= DATE '2025-10-01'
    GROUP BY Product_ID, Store_ID
) sold ON i.Product_ID = sold.Product_ID AND i.Store_ID = sold.Store_ID
WHERE i.Stock_Level > i.Reorder_Level * 2
  AND COALESCE(sold.Units_Sold_90d, 0) < 5
ORDER BY i.Stock_Level DESC;

-- E2. Stock shortages / at-risk of stockout
SELECT i.Product_ID, p.Product_Name, i.Store_ID, i.Stock_Level, i.Reorder_Level
FROM Inventory i JOIN Products p ON i.Product_ID = p.Product_ID
WHERE i.Stock_Level <= i.Reorder_Level
ORDER BY (i.Reorder_Level - i.Stock_Level) DESC;

-- E3. Inventory turnover ratio (approx.) by product
SELECT i.Product_ID, p.Product_Name,
       COALESCE(SUM(sl.Quantity_Sold), 0)                                    AS Units_Sold_Period,
       AVG(i.Stock_Level)                                                    AS Avg_Stock_On_Hand,
       ROUND(COALESCE(SUM(sl.Quantity_Sold), 0) / NULLIF(AVG(i.Stock_Level),0), 2) AS Turnover_Ratio
FROM Inventory i
JOIN Products p ON i.Product_ID = p.Product_ID
LEFT JOIN Sales sl ON sl.Product_ID = i.Product_ID AND sl.Sales_Amount IS NOT NULL
GROUP BY i.Product_ID, p.Product_Name
ORDER BY Turnover_Ratio ASC;

-- E4. Inventory carrying cost by store
SELECT i.Store_ID, s.Store_Name, ROUND(SUM(i.Inventory_Cost), 2) AS Total_Inventory_Cost
FROM Inventory i JOIN Stores s ON i.Store_ID = s.Store_ID
GROUP BY i.Store_ID, s.Store_Name
ORDER BY Total_Inventory_Cost DESC;

-- E5. Days since last restock (operational risk flag)
SELECT i.Product_ID, i.Store_ID, i.Last_Restock_Date,
       (DATE '2026-01-01' - i.Last_Restock_Date) AS Days_Since_Restock
FROM Inventory i
WHERE i.Last_Restock_Date < DATE '2025-06-01'
ORDER BY Days_Since_Restock DESC;

-- =============================================================================
-- F. MARKETING ANALYSIS
-- =============================================================================

-- F1. Campaign ROI ranking
SELECT Campaign_Name, Campaign_Type,
       ROUND(Campaign_Cost, 2)      AS Cost,
       ROUND(Revenue_Generated, 2)   AS Revenue,
       ROUND((Revenue_Generated - Campaign_Cost) / NULLIF(Campaign_Cost,0) * 100, 1) AS ROI_Pct
FROM Campaigns
ORDER BY ROI_Pct DESC;

-- F2. Best performing campaigns by conversion rate
SELECT Campaign_Name, Campaign_Type, Conversion_Rate, Customers_Reached
FROM Campaigns
ORDER BY Conversion_Rate DESC
LIMIT 5;

-- F3. Campaign type efficiency (avg ROI by channel)
SELECT Campaign_Type,
       ROUND(AVG((Revenue_Generated - Campaign_Cost) / NULLIF(Campaign_Cost,0) * 100), 1) AS Avg_ROI_Pct,
       COUNT(*) AS Campaigns_Run
FROM Campaigns
GROUP BY Campaign_Type
ORDER BY Avg_ROI_Pct DESC;

-- F4. Underperforming campaigns (negative ROI — candidates to discontinue)
SELECT Campaign_Name, Campaign_Type, Campaign_Cost, Revenue_Generated
FROM Campaigns
WHERE Revenue_Generated < Campaign_Cost
ORDER BY (Revenue_Generated - Campaign_Cost) ASC;

-- =============================================================================
-- G. RETURNS ANALYSIS
-- =============================================================================

-- G1. Return rate by product category
SELECT p.Category,
       COUNT(DISTINCT r.Return_ID)                              AS Returns,
       COUNT(DISTINCT sl.Transaction_ID)                        AS Total_Transactions,
       ROUND(100.0 * COUNT(DISTINCT r.Return_ID) / NULLIF(COUNT(DISTINCT sl.Transaction_ID),0), 2) AS Return_Rate_Pct
FROM Sales sl
JOIN Products p ON sl.Product_ID = p.Product_ID
LEFT JOIN Returns r ON sl.Transaction_ID = r.Transaction_ID
GROUP BY p.Category
ORDER BY Return_Rate_Pct DESC;

-- G2. Top return reasons
SELECT Return_Reason, COUNT(*) AS Occurrences, ROUND(SUM(Refund_Amount), 2) AS Total_Refunded
FROM Returns
GROUP BY Return_Reason
ORDER BY Occurrences DESC;

-- G3. Refund value as % of gross revenue
SELECT ROUND(SUM(r.Refund_Amount), 2) AS Total_Refunds,
       ROUND(SUM(sl.Sales_Amount), 2)  AS Gross_Revenue,
       ROUND(100.0 * SUM(r.Refund_Amount) / NULLIF(SUM(sl.Sales_Amount),0), 2) AS Refund_Pct_of_Revenue
FROM Returns r
JOIN Sales sl ON r.Transaction_ID = sl.Transaction_ID
WHERE sl.Sales_Amount IS NOT NULL;

-- =============================================================================
-- H. SUPPLIER ANALYSIS
-- =============================================================================

-- H1. Supplier delivery performance vs product profitability
SELECT sup.Supplier_Name, sup.Delivery_Performance, sup.Supplier_Rating,
       ROUND(SUM(sl.Profit), 2) AS Profit_Generated
FROM Sales sl
JOIN Products p ON sl.Product_ID = p.Product_ID
JOIN Suppliers sup ON p.Supplier = sup.Supplier_ID
WHERE sl.Sales_Amount IS NOT NULL
GROUP BY sup.Supplier_Name, sup.Delivery_Performance, sup.Supplier_Rating
ORDER BY Profit_Generated DESC;

-- H2. Underperforming suppliers (low delivery performance, high category revenue exposure)
SELECT sup.Supplier_Name, sup.Category, sup.Delivery_Performance,
       ROUND(SUM(sl.Sales_Amount), 2) AS Revenue_Exposure
FROM Sales sl
JOIN Products p ON sl.Product_ID = p.Product_ID
JOIN Suppliers sup ON p.Supplier = sup.Supplier_ID
WHERE sl.Sales_Amount IS NOT NULL AND sup.Delivery_Performance < 85
GROUP BY sup.Supplier_Name, sup.Category, sup.Delivery_Performance
ORDER BY Revenue_Exposure DESC;

/* =============================================================================
   END OF QUERY LIBRARY — 34 business-focused queries across 8 analysis areas.
   ============================================================================= */
