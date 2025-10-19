from flask import Flask, render_template, request, jsonify, session, redirect, url_for, flash
import numpy as np
import pandas as pd
import math

import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.secret_key = 'your_very_secret_key' # Replace with a real secret key

# --- Database Configuration ---

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
        conn = get_db_connection()
        cursor = conn.cursor()
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


def run_inventory_simulation(initial_inventory, avg_daily_demand, demand_volatility, lead_time_days, num_days, num_simulations):
    all_inventory_levels = np.zeros((num_days + 1, num_simulations))
    all_inventory_levels[0, :] = initial_inventory
    total_stockout_days = 0

    for i in range(num_simulations):
        inventory_levels = list(all_inventory_levels[:, i])
        pending_orders = {}
        reorder_point = avg_daily_demand * lead_time_days

        for day in range(1, num_days + 1):
            # Check for arriving orders
            if day in pending_orders:
                inventory_levels[day-1] += pending_orders.pop(day)

            # Simulate demand
            daily_demand = max(0, np.random.normal(avg_daily_demand, demand_volatility))
            
            # Fulfill demand
            current_inventory = inventory_levels[day-1]
            if current_inventory >= daily_demand:
                inventory_levels[day] = current_inventory - daily_demand
            else:
                inventory_levels[day] = 0
                total_stockout_days += 1

            # Reorder policy
            if inventory_levels[day] < reorder_point and not any(d > day for d in pending_orders.keys()):
                order_quantity = initial_inventory - inventory_levels[day]
                arrival_day = day + lead_time_days
                if arrival_day <= num_days:
                    pending_orders[arrival_day] = order_quantity
        
        all_inventory_levels[:, i] = inventory_levels

    # Analysis
    final_inventory_levels = all_inventory_levels[-1, :]
    prob_of_stockout = (total_stockout_days / (num_days * num_simulations)) * 100
    avg_final_inventory = np.mean(final_inventory_levels)
    confidence_interval_90 = {
        'lower': np.percentile(final_inventory_levels, 5),
        'upper': np.percentile(final_inventory_levels, 95)
    }

    return all_inventory_levels.tolist(), prob_of_stockout, avg_final_inventory, confidence_interval_90


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
        conn = get_db_connection()
        cursor = conn.cursor()
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


import mysql.connector

# --- Database Connection Helper ---
def get_db_connection():
    conn = mysql.connector.connect(
        host=os.getenv("DB_HOST"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASS"),
        database=os.getenv("DB_NAME"),
        port=os.getenv("DB_PORT")
    )
    return conn

# --- Admin Panel Routes ---

@app.route('/admin')
def admin():
    if 'logged_in' in session:
        return redirect(url_for('admin_dashboard'))
    return render_template('admin_login.html')

@app.route('/admin/login', methods=['POST'])
def admin_login():
    if request.form['password'] == 'admin':
        session['logged_in'] = True
        return redirect(url_for('admin_dashboard'))
    else:
        flash('Wrong password!')
        return redirect(url_for('admin'))

@app.route('/admin/logout')
def admin_logout():
    session.pop('logged_in', None)
    return redirect(url_for('index'))

@app.route('/admin/dashboard')
def admin_dashboard():
    if 'logged_in' not in session:
        return redirect(url_for('admin'))
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
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
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(f"TRUNCATE TABLE {table}")
        conn.commit()
        cursor.close()
        conn.close()
        flash(f'All data from {table} has been deleted.')
    
    return redirect(url_for('admin_dashboard'))


if __name__ == '__main__':
    app.run(debug=True)
