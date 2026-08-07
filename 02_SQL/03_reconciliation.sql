/* =============================================================================
   RETAIL_ANALYTICS_DB — DATA RECOVERY & RECONCILIATION LOGIC
   Client: ApexMart Retail Ltd.
   Companion to: 05_Reports/Data_Quality_Assessment_Report
   Purpose: Detection queries used to identify and quantify each data-quality
            issue seeded in the raw extracts, plus the reconciliation logic
            used to produce a "Clean" analytics layer.
   ============================================================================= */

-- =============================================================================
-- 1. DUPLICATE TRANSACTIONS
-- =============================================================================
SELECT Transaction_ID, COUNT(*) AS Occurrences
FROM Sales
GROUP BY Transaction_ID
HAVING COUNT(*) > 1;

-- Resolution: de-duplicate keeping one instance per Transaction_ID
CREATE VIEW Sales_Deduplicated AS
SELECT DISTINCT ON (Transaction_ID) *
FROM Sales
ORDER BY Transaction_ID;

-- =============================================================================
-- 2. MISSING CUSTOMER RECORDS (orphaned foreign keys)
-- =============================================================================
SELECT sl.Customer_ID, COUNT(*) AS Affected_Transactions
FROM Sales sl
LEFT JOIN Customers c ON sl.Customer_ID = c.Customer_ID
WHERE c.Customer_ID IS NULL
GROUP BY sl.Customer_ID;

-- Resolution: route to an "Unmapped Customer" holding record so revenue is not
-- silently dropped from reporting while the source-system fix is implemented
INSERT INTO Customers (Customer_ID, Customer_Name, Customer_Segment, Customer_Value_Category)
SELECT DISTINCT sl.Customer_ID, 'UNMAPPED - Pending CRM Sync', 'Occasional', 'Low Value'
FROM Sales sl
LEFT JOIN Customers c ON sl.Customer_ID = c.Customer_ID
WHERE c.Customer_ID IS NULL;

-- =============================================================================
-- 3. INVALID / UNMAPPED STORE CODES
-- =============================================================================
SELECT sl.Store_ID, COUNT(*) AS Affected_Transactions,
       ROUND(SUM(sl.Sales_Amount), 2) AS Revenue_At_Risk
FROM Sales sl
LEFT JOIN Stores s ON sl.Store_ID = s.Store_ID
WHERE s.Store_ID IS NULL
GROUP BY sl.Store_ID;

-- Resolution: quarantine into an exceptions table for manual store-code mapping
-- by the Finance/Ops team rather than allocating to an incorrect branch
CREATE TABLE Sales_Exceptions_Unmapped_Store AS
SELECT sl.*
FROM Sales sl
LEFT JOIN Stores s ON sl.Store_ID = s.Store_ID
WHERE s.Store_ID IS NULL;

-- =============================================================================
-- 4. INCORRECT / MISSING PRODUCT MAPPINGS
-- =============================================================================
SELECT sl.Product_ID, COUNT(*) AS Affected_Transactions
FROM Sales sl
LEFT JOIN Products p ON sl.Product_ID = p.Product_ID
WHERE p.Product_ID IS NULL
GROUP BY sl.Product_ID;

-- Resolution: quarantine for catalog-team remediation (root cause: POS-to-catalog
-- sync job failure identified during the December system migration — see report)
CREATE TABLE Sales_Exceptions_Unmapped_Product AS
SELECT sl.*
FROM Sales sl
LEFT JOIN Products p ON sl.Product_ID = p.Product_ID
WHERE p.Product_ID IS NULL;

-- =============================================================================
-- 5. REVENUE MISMATCHES (Sales_Amount != Unit_Price*Qty - Discount)
-- =============================================================================
SELECT Transaction_ID, Unit_Price, Quantity_Sold, Discount, Sales_Amount,
       ROUND(Unit_Price * Quantity_Sold - Discount, 2) AS Expected_Sales_Amount,
       ROUND(Sales_Amount - (Unit_Price * Quantity_Sold - Discount), 2) AS Variance
FROM Sales
WHERE Sales_Amount IS NOT NULL
  AND ABS(Sales_Amount - (Unit_Price * Quantity_Sold - Discount)) > 1.00;

-- Resolution: recompute Sales_Amount from source fields where variance exceeds
-- a ₦1 rounding tolerance, and log the correction for audit
CREATE VIEW Sales_Amount_Corrected AS
SELECT *,
       CASE WHEN ABS(Sales_Amount - (Unit_Price * Quantity_Sold - Discount)) > 1.00
            THEN ROUND(Unit_Price * Quantity_Sold - Discount, 2)
            ELSE Sales_Amount
       END AS Sales_Amount_Reconciled
FROM Sales;

-- =============================================================================
-- 6. MISSING PAYMENTS (Sales vs Payments reconciliation)
-- =============================================================================
SELECT Transaction_ID, Transaction_Date, Store_ID,
       ROUND(Unit_Price * Quantity_Sold - Discount, 2) AS Expected_Payment
FROM Sales
WHERE Sales_Amount IS NULL;

-- Resolution: impute the expected payment from source fields as an interim
-- reporting value, flagged for Finance confirmation against the payment gateway
CREATE VIEW Sales_Revenue_Vs_Payments_Reconciliation AS
SELECT Transaction_ID, Transaction_Date, Store_ID,
       ROUND(Unit_Price * Quantity_Sold - Discount, 2) AS Reconciled_Revenue,
       CASE WHEN Sales_Amount IS NULL THEN 'Missing Payment Record - Imputed'
            ELSE 'Payment Confirmed' END AS Reconciliation_Status
FROM Sales;

-- =============================================================================
-- 7. SALES vs RETURNS RECONCILIATION (orphaned return records)
-- =============================================================================
SELECT r.Return_ID, r.Transaction_ID
FROM Returns r
LEFT JOIN Sales sl ON r.Transaction_ID = sl.Transaction_ID
WHERE sl.Transaction_ID IS NULL;

-- =============================================================================
-- 8. SALES vs INVENTORY RECONCILIATION
--    (products actively selling at a store with no inventory record at all —
--     signals a missing stock-count file for that store/product combination)
-- =============================================================================
SELECT DISTINCT sl.Product_ID, sl.Store_ID
FROM Sales sl
LEFT JOIN Inventory i ON sl.Product_ID = i.Product_ID AND sl.Store_ID = i.Store_ID
WHERE i.Inventory_ID IS NULL
  AND sl.Store_ID IN (SELECT Store_ID FROM Stores)   -- exclude already-unmapped stores
  AND sl.Product_ID IN (SELECT Product_ID FROM Products); -- exclude already-unmapped products

-- =============================================================================
-- 9. CLEAN ANALYTICS VIEW
--    Combines all corrections above into a single "reporting-ready" view.
--    This is the view the SQL queries in 02_analytics_queries.sql should be
--    pointed at once the reconciliation pipeline runs on a schedule.
-- =============================================================================
CREATE VIEW Sales_Clean AS
SELECT DISTINCT ON (sl.Transaction_ID)
       sl.Transaction_ID,
       sl.Transaction_Date,
       sl.Customer_ID,
       sl.Product_ID,
       sl.Store_ID,
       sl.Quantity_Sold,
       sl.Unit_Price,
       sl.Discount,
       COALESCE(
           CASE WHEN ABS(sl.Sales_Amount - (sl.Unit_Price * sl.Quantity_Sold - sl.Discount)) > 1.00
                THEN ROUND(sl.Unit_Price * sl.Quantity_Sold - sl.Discount, 2)
                ELSE sl.Sales_Amount END,
           ROUND(sl.Unit_Price * sl.Quantity_Sold - sl.Discount, 2)
       ) AS Sales_Amount_Clean,
       sl.Cost_Amount
FROM Sales sl
JOIN Stores st   ON sl.Store_ID = st.Store_ID
JOIN Products p  ON sl.Product_ID = p.Product_ID
ORDER BY sl.Transaction_ID;

/* =============================================================================
   END OF RECONCILIATION MODULE
   ============================================================================= */
