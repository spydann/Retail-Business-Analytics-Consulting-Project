/* =============================================================================
   RETAIL_ANALYTICS_DB — DATABASE SCHEMA
   Client: ApexMart Retail Ltd.
   Engagement: Retail Profitability & Performance Optimization
   Purpose: Enterprise-style relational schema underpinning the analytics
            and business intelligence work performed in this engagement.
   Notes:
     - Written in ANSI SQL / PostgreSQL dialect. Minor syntax changes apply
       for MySQL / SQL Server (e.g. AUTOINCREMENT vs IDENTITY vs SERIAL).
     - Referential integrity is intentionally enforced here so that the
       data-quality issues documented in Section 7 (05_Reports/
       Data_Quality_Assessment_Report) surface as constraint violations
       when the raw CSV extracts are loaded "as-is" — this is what a real
       ETL load into a governed warehouse would flag.
   ============================================================================= */

CREATE DATABASE IF NOT EXISTS Retail_Analytics_DB;
USE Retail_Analytics_DB;

-- -----------------------------------------------------------------------------
-- DIMENSION: STORES
-- -----------------------------------------------------------------------------
CREATE TABLE Stores (
    Store_ID              VARCHAR(10)     PRIMARY KEY,
    Store_Name            VARCHAR(150)    NOT NULL,
    Region                VARCHAR(50)     NOT NULL,
    City                  VARCHAR(50)     NOT NULL,
    Store_Size            VARCHAR(20)     NOT NULL CHECK (Store_Size IN ('Small','Medium','Large','Flagship')),
    Number_of_Employees    INT             NOT NULL CHECK (Number_of_Employees > 0),
    Opening_Date           DATE            NOT NULL
);

-- -----------------------------------------------------------------------------
-- DIMENSION: SUPPLIERS
-- -----------------------------------------------------------------------------
CREATE TABLE Suppliers (
    Supplier_ID            VARCHAR(10)     PRIMARY KEY,
    Supplier_Name          VARCHAR(150)    NOT NULL,
    Category               VARCHAR(50)     NOT NULL,
    Delivery_Performance   DECIMAL(5,2)    NOT NULL CHECK (Delivery_Performance BETWEEN 0 AND 100),
    Supplier_Rating        DECIMAL(3,1)    NOT NULL CHECK (Supplier_Rating BETWEEN 0 AND 5)
);

-- -----------------------------------------------------------------------------
-- DIMENSION: PRODUCTS
-- -----------------------------------------------------------------------------
CREATE TABLE Products (
    Product_ID          VARCHAR(10)     PRIMARY KEY,
    Product_Name        VARCHAR(150)    NOT NULL,
    Category             VARCHAR(50)     NOT NULL,
    Sub_Category         VARCHAR(50)     NOT NULL,
    Supplier             VARCHAR(10)     NOT NULL,
    Cost_Price            DECIMAL(12,2)   NOT NULL CHECK (Cost_Price >= 0),
    Selling_Price         DECIMAL(12,2)   NOT NULL CHECK (Selling_Price >= 0),
    Product_Status        VARCHAR(20)     NOT NULL CHECK (Product_Status IN ('Active','Discontinued','New')),
    CONSTRAINT fk_products_supplier FOREIGN KEY (Supplier) REFERENCES Suppliers(Supplier_ID)
);

-- -----------------------------------------------------------------------------
-- DIMENSION: CUSTOMERS
-- -----------------------------------------------------------------------------
CREATE TABLE Customers (
    Customer_ID               VARCHAR(10)     PRIMARY KEY,
    Customer_Name             VARCHAR(150)    NOT NULL,
    Gender                    VARCHAR(10),
    Age_Group                 VARCHAR(10),
    Customer_Segment          VARCHAR(20)     CHECK (Customer_Segment IN ('Regular','Premium','Occasional','Corporate')),
    Location                  VARCHAR(50),
    Customer_Since            DATE,
    Customer_Value_Category   VARCHAR(20)     CHECK (Customer_Value_Category IN ('High Value','Medium Value','Low Value'))
);

-- -----------------------------------------------------------------------------
-- FACT: SALES TRANSACTIONS
-- -----------------------------------------------------------------------------
CREATE TABLE Sales (
    Transaction_ID     VARCHAR(15)     PRIMARY KEY,
    Transaction_Date    DATE            NOT NULL,
    Customer_ID         VARCHAR(10)     NOT NULL,
    Product_ID          VARCHAR(10)     NOT NULL,
    Store_ID             VARCHAR(10)     NOT NULL,
    Quantity_Sold        INT             NOT NULL CHECK (Quantity_Sold > 0),
    Unit_Price            DECIMAL(12,2)   NOT NULL,
    Discount              DECIMAL(12,2)   DEFAULT 0,
    Sales_Amount           DECIMAL(14,2),                 -- nullable: see missing-payment DQ scenario
    Cost_Amount             DECIMAL(14,2)   NOT NULL,
    Profit                  DECIMAL(14,2),
    CONSTRAINT fk_sales_customer FOREIGN KEY (Customer_ID) REFERENCES Customers(Customer_ID),
    CONSTRAINT fk_sales_product  FOREIGN KEY (Product_ID)  REFERENCES Products(Product_ID),
    CONSTRAINT fk_sales_store    FOREIGN KEY (Store_ID)    REFERENCES Stores(Store_ID)
);

-- -----------------------------------------------------------------------------
-- FACT: INVENTORY (SNAPSHOT, GRAIN: PRODUCT x STORE)
-- -----------------------------------------------------------------------------
CREATE TABLE Inventory (
    Inventory_ID        VARCHAR(15)     PRIMARY KEY,
    Product_ID           VARCHAR(10)     NOT NULL,
    Store_ID              VARCHAR(10)     NOT NULL,
    Stock_Level            INT             NOT NULL CHECK (Stock_Level >= 0),
    Reorder_Level          INT             NOT NULL,
    Inventory_Cost          DECIMAL(14,2)   NOT NULL,
    Last_Restock_Date       DATE,
    CONSTRAINT fk_inventory_product FOREIGN KEY (Product_ID) REFERENCES Products(Product_ID),
    CONSTRAINT fk_inventory_store   FOREIGN KEY (Store_ID)   REFERENCES Stores(Store_ID)
);

-- -----------------------------------------------------------------------------
-- FACT: MARKETING CAMPAIGNS
-- -----------------------------------------------------------------------------
CREATE TABLE Campaigns (
    Campaign_ID         VARCHAR(10)     PRIMARY KEY,
    Campaign_Name        VARCHAR(150)    NOT NULL,
    Campaign_Type          VARCHAR(30)     NOT NULL,
    Campaign_Cost           DECIMAL(14,2)   NOT NULL,
    Customers_Reached        INT             NOT NULL,
    Revenue_Generated          DECIMAL(14,2)   NOT NULL,
    Conversion_Rate              DECIMAL(6,4)    NOT NULL
);

-- -----------------------------------------------------------------------------
-- FACT: RETURNS
-- -----------------------------------------------------------------------------
CREATE TABLE Returns (
    Return_ID           VARCHAR(15)     PRIMARY KEY,
    Transaction_ID        VARCHAR(15)     NOT NULL,
    Return_Date            DATE            NOT NULL,
    Return_Reason            VARCHAR(50),
    Refund_Amount              DECIMAL(14,2)   NOT NULL,
    CONSTRAINT fk_returns_txn FOREIGN KEY (Transaction_ID) REFERENCES Sales(Transaction_ID)
);

-- -----------------------------------------------------------------------------
-- INDEXES to support the analytical query workload in 02_analytics_queries.sql
-- -----------------------------------------------------------------------------
CREATE INDEX idx_sales_date        ON Sales(Transaction_Date);
CREATE INDEX idx_sales_store       ON Sales(Store_ID);
CREATE INDEX idx_sales_product     ON Sales(Product_ID);
CREATE INDEX idx_sales_customer    ON Sales(Customer_ID);
CREATE INDEX idx_inventory_store   ON Inventory(Store_ID);
CREATE INDEX idx_returns_txn       ON Returns(Transaction_ID);

/* -----------------------------------------------------------------------------
   ENTITY RELATIONSHIP SUMMARY
   -----------------------------------------------------------------------------
   Stores      (1) ────< (M) Sales
   Products    (1) ────< (M) Sales
   Customers   (1) ────< (M) Sales
   Suppliers   (1) ────< (M) Products
   Stores      (1) ────< (M) Inventory
   Products    (1) ────< (M) Inventory
   Sales       (1) ────< (M) Returns
   Campaigns are intentionally NOT foreign-keyed to Sales — ApexMart does not
   currently capture a Campaign_ID on the POS transaction, which is itself one
   of the reporting-fragmentation problems raised in Section 2 of the main
   report and Recommendation R4 in the Business Consulting Report.
   ============================================================================= */
