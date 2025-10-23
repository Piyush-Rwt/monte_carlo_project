CREATE DATABASE IF NOT EXISTS monte_carlo_database;

USE monte_carlo_database;

CREATE TABLE stock_simulations (
    id INT AUTO_INCREMENT PRIMARY KEY,
    simulation_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    initial_price DECIMAL(10, 2),
    annual_volatility DECIMAL(5, 2),
    num_days INT,
    num_simulations INT,
    target_price DECIMAL(10, 2),
    avg_final_price DECIMAL(10, 2),
    prob_of_loss DECIMAL(5, 2),
    confidence_interval_lower DECIMAL(10, 2),
    confidence_interval_upper DECIMAL(10, 2),
    value_at_risk DECIMAL(10, 2)
);

CREATE TABLE inventory_simulations (
    id INT AUTO_INCREMENT PRIMARY KEY,
    simulation_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    initial_inventory INT,
    avg_daily_demand INT,
    demand_volatility DECIMAL(5, 2),
    lead_time_days INT,
    num_days INT,
    num_simulations INT,
    prob_of_stockout DECIMAL(5, 2),
    avg_final_inventory DECIMAL(10, 2),
    confidence_interval_lower DECIMAL(10, 2),
    confidence_interval_upper DECIMAL(10, 2)
);
