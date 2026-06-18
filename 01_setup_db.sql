-- ================================================================
-- 01_setup_db.sql
-- Creates database, dimensions, fact table and ETL control table
-- ================================================================

CREATE DATABASE IF NOT EXISTS food_delivery_scd;
USE food_delivery_scd;

-- Customer Dimension
DROP TABLE IF EXISTS dim_customer;
CREATE TABLE dim_customer (
    customer_key          INT AUTO_INCREMENT PRIMARY KEY,
    customer_id           VARCHAR(20) NOT NULL,
    name                  VARCHAR(100),
    phone                 VARCHAR(20),      -- SCD1
    email                 VARCHAR(150),     -- SCD1
    city                  VARCHAR(80),      -- SCD2
    area                  VARCHAR(80),
    loyalty_tier          VARCHAR(20),      -- SCD2
    platform              VARCHAR(20),
    effective_start_date  DATE,
    effective_end_date    DATE,
    is_current            TINYINT(1) DEFAULT 1
);

-- Restaurant Dimension
DROP TABLE IF EXISTS dim_restaurant;
CREATE TABLE dim_restaurant (
    restaurant_key        INT AUTO_INCREMENT PRIMARY KEY,
    restaurant_id         VARCHAR(20) NOT NULL,
    name                  VARCHAR(150),
    owner_name            VARCHAR(100),     -- SCD1
    city                  VARCHAR(80),
    area                  VARCHAR(80),
    cuisine_type          VARCHAR(80),      -- SCD2
    avg_rating            DECIMAL(3,1),     -- SCD1
    price_range           VARCHAR(20),      -- SCD2
    effective_start_date  DATE,
    effective_end_date    DATE,
    is_current            TINYINT(1) DEFAULT 1
);

-- Menu Item Dimension
DROP TABLE IF EXISTS dim_menu_item;
CREATE TABLE dim_menu_item (
    item_key              INT AUTO_INCREMENT PRIMARY KEY,
    item_id               VARCHAR(20) NOT NULL,
    restaurant_id         VARCHAR(20),
    item_name             VARCHAR(150),
    category              VARCHAR(80),      -- SCD2
    price                 DECIMAL(10,2),    -- SCD1
    is_veg                TINYINT(1),
    effective_start_date  DATE,
    effective_end_date    DATE,
    is_current            TINYINT(1) DEFAULT 1
);

-- Delivery Agent Dimension
DROP TABLE IF EXISTS dim_agent;
CREATE TABLE dim_agent (
    agent_key             INT AUTO_INCREMENT PRIMARY KEY,
    agent_id              VARCHAR(20) NOT NULL,
    name                  VARCHAR(100),
    phone                 VARCHAR(20),      -- SCD1
    city                  VARCHAR(80),
    vehicle_type          VARCHAR(30),      -- SCD2
    status                VARCHAR(20),      -- SCD2
    total_deliveries      INT,              -- SCD1
    effective_start_date  DATE,
    effective_end_date    DATE,
    is_current            TINYINT(1) DEFAULT 1
);

-- Orders Fact Table (Incremental Load Only)
DROP TABLE IF EXISTS fact_orders;
CREATE TABLE fact_orders (
    order_id          VARCHAR(20) PRIMARY KEY,
    customer_id       VARCHAR(20),
    restaurant_id     VARCHAR(20),
    item_id           VARCHAR(20),
    order_date        DATE,
    amount            DECIMAL(10,2),
    payment_mode      VARCHAR(30),
    delivery_status   VARCHAR(20),
    agent_id          VARCHAR(20),
    loaded_at         TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ETL Control Table
DROP TABLE IF EXISTS etl_control;
CREATE TABLE etl_control (
    source_name      VARCHAR(50) PRIMARY KEY,
    last_loaded_date DATE
);

SELECT 'All tables created successfully' AS message;