from flask import Flask, render_template, request, jsonify, session, redirect, url_for, flash
import numpy as np
import pandas as pd
import math
from dotenv import load_dotenv
import os

load_dotenv()  # this reads the .env file

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY')

# --- Database Configuration ---
app.config['MYSQL_HOST'] = os.getenv('LOCAL_DB_HOST')
app.config['MYSQL_USER'] = os.getenv('LOCAL_DB_USER')
app.config['MYSQL_PASSWORD'] = os.getenv('LOCAL_DB_PASSWORD')
app.config['MYSQL_DB'] = os.getenv('LOCAL_DB_NAME')

def run_monte_carlo(initial_price, volatility, num_days, num_simulations):
    simulations = np.zeros((num_days + 1, num_simulations))
    simulations[0, :] = initial_price
    for i in range(num_simulations):
        for j in range(1, num_days + 1):
            random_shock = np.random.normal(0, volatility)
            simulations[j, i] = simulations[j - 1, i] * (1 + random_shock)
    return simulations

def analyze_results(simulations, target_price, initial_price):
    final_prices = simulations[-1, :]
    avg_final_price = np.mean(final_prices)
    best_case_price = np.max(final_prices)
    worst_case_price = np.min(final_prices)
    
    probability = None
    if target_price is not None:
        probability = np.sum(final_prices >= target_price) / len(final_prices) * 100

    # Risk Analysis Calculations
    prob_of_loss = np.sum(final_prices < initial_price) / len(final_prices) * 100
    confidence_interval_90 = {
        'lower': np.percentile(final_prices, 5),
        'upper': np.percentile(final_prices, 95)
    }
    value_at_risk_95 = initial_price - np.percentile(final_prices, 5)

    return avg_final_price, best_case_price, worst_case_price, probability, final_prices, prob_of_loss, confidence_interval_90, value_at_risk_95

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/stock_simulation')
def stock_simulation_page():
    return render_template('stock_simulation.html')

@app.route('/inventory_simulation')
def inventory_simulation_page():
    return render_template('inventory.html')

import psycopg2.extras

# --- Database Connection Helper ---
def get_db_connection():
    conn = None
    if os.getenv("RENDER") == "true":
        # --- Render PostgreSQL connection ---
        db_url = os.getenv("DATABASE_URL")
        if not db_url:
            raise ValueError("DATABASE_URL is not set in the Render environment.")
        conn = psycopg2.connect(db_url)
        cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    else:
        # --- Local MySQL connection ---
        conn = mysql.connector.connect(
            host=app.config['MYSQL_HOST'],
            user=app.config['MYSQL_USER'],
            password=app.config['MYSQL_PASSWORD'],
            database=app.config['MYSQL_DB']
        )
        cursor = conn.cursor(dictionary=True)
    return conn, cursor

@app.route('/simulate', methods=['POST'])
def simulate():
    data = request.get_json()
    initial_price = float(data['initial_price'])
    annual_volatility = float(data['volatility']) / 100
    daily_volatility = annual_volatility / math.sqrt(252)
    num_days = int(data['num_days'])
    num_simulations = int(data['num_simulations'])
    target_price = float(data['target_price']) if data.get('target_price') else None

    simulations = run_monte_carlo(initial_price, daily_volatility, num_days, num_simulations)
    avg_final_price, best_case, worst_case, probability, final_prices, prob_of_loss, ci_90, var_95 = analyze_results(simulations, target_price, initial_price)

    # Save results to database
    try:
        conn, cursor = get_db_connection()
        sql = """INSERT INTO stock_simulations (initial_price, annual_volatility, num_days, num_simulations, target_price, avg_final_price, prob_of_loss, confidence_interval_lower, confidence_interval_upper, value_at_risk) 
                 VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"""
        val = (initial_price, annual_volatility * 100, num_days, num_simulations, target_price, avg_final_price, prob_of_loss, ci_90['lower'], ci_90['upper'], var_95)
        cursor.execute(sql, val)
        conn.commit()
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"Database error: {e}")

    return jsonify({
        'simulations': simulations.tolist(),
        'avg_final_price': avg_final_price,
        'best_case_price': best_case,
        'worst_case_price': worst_case,
        'probability': probability,
        'prob_of_loss': prob_of_loss,
        'confidence_interval_90': ci_90,
        'value_at_risk_95': var_95
    })


@app.route('/simulate_inventory', methods=['POST'])
def simulate_inventory():
    data = request.get_json()
    initial_inventory = int(data['initial_inventory'])
    avg_daily_demand = int(data['avg_daily_demand'])
    demand_volatility = float(data['demand_volatility'])
    lead_time_days = int(data['lead_time_days'])
    num_days = int(data['num_days'])
    num_simulations = int(data['num_simulations'])

    inventory_sims, prob_stockout, avg_final, ci_90 = run_inventory_simulation(
        initial_inventory, avg_daily_demand, demand_volatility, lead_time_days, num_days, num_simulations
    )

    # Save results to database
    try:
        conn, cursor = get_db_connection()
        sql = """INSERT INTO inventory_simulations (initial_inventory, avg_daily_demand, demand_volatility, lead_time_days, num_days, num_simulations, prob_of_stockout, avg_final_inventory, confidence_interval_lower, confidence_interval_upper) 
                 VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"""
        val = (initial_inventory, avg_daily_demand, demand_volatility, lead_time_days, num_days, num_simulations, prob_stockout, avg_final, ci_90['lower'], ci_90['upper'])
        cursor.execute(sql, val)
        conn.commit()
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"Database error: {e}")

    return jsonify({
        'inventory_simulations': inventory_sims,
        'prob_of_stockout': prob_stockout,
        'avg_final_inventory': avg_final,
        'confidence_interval_90': ci_90
    })

@app.route('/admin/dashboard')
def admin_dashboard():
    if 'logged_in' not in session:
        return redirect(url_for('admin'))
    
    conn, cursor = get_db_connection()
    
    cursor.execute("SELECT * FROM stock_simulations ORDER BY simulation_timestamp DESC")
    stock_data = cursor.fetchall()
    
    cursor.execute("SELECT * FROM inventory_simulations ORDER BY simulation_timestamp DESC")
    inventory_data = cursor.fetchall()
    
    cursor.close()
    conn.close()
    
    return render_template('admin_dashboard.html', stock_data=stock_data, inventory_data=inventory_data)

@app.route('/admin/delete/<table>', methods=['POST'])
def delete_data(table):
    if 'logged_in' not in session:
        return redirect(url_for('admin'))
    
    if table in ['stock_simulations', 'inventory_simulations']:
        conn, cursor = get_db_connection()
        cursor.execute(f"TRUNCATE TABLE {table}")
        conn.commit()
        cursor.close()
        conn.close()
        flash(f'All data from {table} has been deleted.')
    
    return redirect(url_for('admin_dashboard'))


if __name__ == '__main__':
    app.run(debug=True)
