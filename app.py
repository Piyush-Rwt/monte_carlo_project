from flask import Flask, render_template, request, jsonify, session, redirect, url_for, flash
import numpy as np
import pandas as pd
import math
import os
import psycopg2
import psycopg2.extras # For dictionary cursor
from urllib.parse import urlparse
from dotenv import load_dotenv
import yfinance as yf
from flask_caching import Cache

# Load environment variables (optional for local testing)
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'default_secret')

# --- Cache Configuration ---
cache = Cache(app, config={'CACHE_TYPE': 'simple'})

# --- Database Connection Helper ---
def get_db_connection():
    try:
        # Parse the database URL from the environment variable
        db_url = os.getenv("DATABASE_URL")
        if not db_url:
            raise Exception("DATABASE_URL environment variable not set")
            
        result = urlparse(db_url)
        
        conn = psycopg2.connect(
            dbname=result.path[1:],
            user=result.username,
            password=result.password,
            host=result.hostname,
            port=result.port
        )
        # Use a cursor factory that returns dictionaries
        cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        return conn, cursor
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return None, None


# --- Monte Carlo Simulation Functions ---
def run_monte_carlo(initial_price, volatility, num_days, num_simulations):
    if initial_price <= 0 or volatility <= 0 or num_days <= 0 or num_simulations <= 0:
        return None
    simulations = np.zeros((num_days + 1, num_simulations))
    simulations[0, :] = initial_price
    for i in range(num_simulations):
        for j in range(1, num_days + 1):
            random_shock = np.random.normal(0, volatility)
            simulations[j, i] = simulations[j - 1, i] * (1 + random_shock)
    return simulations

def run_inventory_simulation(initial_inventory, avg_daily_demand, demand_volatility, lead_time_days, num_days, num_simulations):
    if initial_inventory < 0 or avg_daily_demand < 0 or demand_volatility < 0 or lead_time_days <= 0 or num_days <= 0 or num_simulations <= 0:
        return None, None, None, None
    inventory_sims = np.zeros((num_days + 1, num_simulations))
    inventory_sims[0, :] = initial_inventory
    stockout_simulations = np.zeros(num_simulations)

    for i in range(num_simulations):
        stockout_event = False
        for j in range(1, num_days + 1):
            daily_demand = np.random.normal(avg_daily_demand, demand_volatility)
            if inventory_sims[j-1, i] > daily_demand:
                inventory_sims[j, i] = inventory_sims[j-1, i] - daily_demand
            else:
                inventory_sims[j, i] = 0
                if not stockout_event:
                    stockout_simulations[i] = 1
                    stockout_event = True
            
            # Replenishment
            if j % lead_time_days == 0:
                inventory_sims[j, i] += avg_daily_demand * lead_time_days

    prob_of_stockout = np.sum(stockout_simulations) / num_simulations * 100
    avg_final_inventory = np.mean(inventory_sims[-1, :])
    confidence_interval_90 = {
        'lower': np.percentile(inventory_sims[-1, :], 5),
        'upper': np.percentile(inventory_sims[-1, :], 95)
    }

    return inventory_sims.tolist(), prob_of_stockout, avg_final_inventory, confidence_interval_90

def analyze_results(simulations, target_price, initial_price):
    if simulations is None or len(simulations) == 0:
        return None, None, None, None, None, None, None, None
    final_prices = simulations[-1, :]
    avg_final_price = np.mean(final_prices)
    best_case_price = np.max(final_prices)
    worst_case_price = np.min(final_prices)
    
    probability = None
    if target_price is not None:
        probability = np.sum(final_prices >= target_price) / len(final_prices) * 100

    prob_of_loss = np.sum(final_prices < initial_price) / len(final_prices) * 100
    confidence_interval_90 = {
        'lower': np.percentile(final_prices, 5),
        'upper': np.percentile(final_prices, 95)
    }
    value_at_risk_95 = initial_price - np.percentile(final_prices, 5)

    return avg_final_price, best_case_price, worst_case_price, probability, final_prices, prob_of_loss, confidence_interval_90, value_at_risk_95


# --- Routes ---
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
    try:
        data = request.get_json()
        initial_price = float(data['initial_price'])
        annual_volatility = float(data['volatility']) / 100
        daily_volatility = annual_volatility / math.sqrt(252)
        num_days = int(data['num_days'])
        num_simulations = int(data['num_simulations'])
        target_price = float(data['target_price']) if data.get('target_price') else None

        simulations = run_monte_carlo(initial_price, daily_volatility, num_days, num_simulations)
        avg_final_price, best_case, worst_case, probability, final_prices, prob_of_loss, ci_90, var_95 = analyze_results(
            simulations, target_price, initial_price
        )

        if simulations is None:
            return jsonify({'error': 'Invalid input for simulation.'}), 400

        try:
            conn, cursor = get_db_connection()
            if conn is None:
                raise Exception("Database not connected")

            sql = """INSERT INTO stock_simulations 
                     (initial_price, annual_volatility, num_days, num_simulations, target_price, avg_final_price, 
                      prob_of_loss, confidence_interval_lower, confidence_interval_upper, value_at_risk) 
                     VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"""
            val = (
                initial_price, annual_volatility * 100, num_days, num_simulations, target_price, 
                avg_final_price, prob_of_loss, ci_90['lower'], ci_90['upper'], var_95
            )
            cursor.execute(sql, val)
            conn.commit()
            cursor.close()
            conn.close()
        except Exception as e:
            print(f"❌ Database insert error: {e}")
            return jsonify({'error': f'Database insert error: {e}'}), 500

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
    except (ValueError, KeyError) as e:
        return jsonify({'error': f'Invalid input: {e}'}), 400

@app.route('/simulate_inventory', methods=['POST'])
def simulate_inventory():
    try:
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

        if inventory_sims is None:
            return jsonify({'error': 'Invalid input for simulation.'}), 400

        try:
            conn, cursor = get_db_connection()
            if conn is None:
                raise Exception("Database not connected")

            sql = """INSERT INTO inventory_simulations 
                     (initial_inventory, avg_daily_demand, demand_volatility, lead_time_days, num_days, num_simulations, 
                      prob_of_stockout, avg_final_inventory, confidence_interval_lower, confidence_interval_upper) 
                     VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"""
            val = (
                initial_inventory, avg_daily_demand, demand_volatility, lead_time_days, num_days, num_simulations, 
                prob_stockout, avg_final, ci_90['lower'], ci_90['upper']
            )
            cursor.execute(sql, val)
            conn.commit()
            cursor.close()
            conn.close()
        except Exception as e:
            print(f"❌ Database insert error: {e}")
            return jsonify({'error': f'Database insert error: {e}'}), 500

        return jsonify({
            'inventory_simulations': inventory_sims,
            'prob_of_stockout': prob_stockout,
            'avg_final_inventory': avg_final,
            'confidence_interval_90': ci_90
        })
    except (ValueError, KeyError) as e:
        return jsonify({'error': f'Invalid input: {e}'}), 400

@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if request.method == 'POST':
        password = request.form.get('password')
        # This is a simple, insecure password check for demonstration purposes.
        # In a real application, use a proper authentication library and hashed passwords.
        if password == os.getenv('ADMIN_PASSWORD', 'password'):
            session['logged_in'] = True
            return redirect(url_for('admin_dashboard'))
        else:
            flash('Invalid password.')
            return redirect(url_for('admin'))
    
    # If GET request or failed login, show the login page
    return render_template('admin_login.html')

@app.route('/admin/logout')
def admin_logout():
    session.pop('logged_in', None)
    return redirect(url_for('index'))


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

@app.route('/real-stocks')
def real_stocks():
    return render_template('real_stocks.html')

@app.route('/real-stocks/<symbol>')
@cache.cached(timeout=1800)
def get_stock_price(symbol):
    try:
        stock = yf.Ticker(symbol)
        price = stock.history(period='1d')['Close'].iloc[0]
        return jsonify({'price': price})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/simulate_real_stock/<symbol>')
def simulate_real_stock(symbol):
    try:
        stock = yf.Ticker(symbol)
        hist = stock.history(period="6mo")

        if hist.empty:
            return jsonify({'error': 'Could not retrieve historical data for the stock.'}), 404
        
        # Calculate daily returns and volatility
        hist['returns'] = hist['Close'].pct_change()
        daily_volatility = hist['returns'].std()
        
        initial_price = hist['Close'].iloc[-1]
        num_days = 30
        num_simulations = 1000
        
        simulations = run_monte_carlo(initial_price, daily_volatility, num_days, num_simulations)
        avg_final_price, best_case, worst_case, _, _, prob_of_loss, ci_90, _ = analyze_results(simulations, None, initial_price)
        
        risk_level = get_risk_level(prob_of_loss, daily_volatility)

        return jsonify({
            'current_price': initial_price,
            'confidence_range': ci_90,
            'prob_of_loss': prob_of_loss,
            'risk_level': risk_level,
            'simulations': simulations.tolist(),
            'historical_data': hist['Close'].tolist()
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def get_risk_level(prob_of_loss, volatility):
    if prob_of_loss > 60 or volatility > 0.03:
        return "High"
    elif prob_of_loss > 45 or volatility > 0.015:
        return "Medium"
    else:
        return "Low"

# --- Test Route for DB Connection ---
@app.route('/testdb')
def test_db():
    try:
        conn, cursor = get_db_connection()
        cursor.execute("SELECT NOW() AS current_time;")
        result = cursor.fetchone()
        cursor.close()
        conn.close()
        return jsonify({"status": "✅ Connected to PostgreSQL", "time": result['current_time']})
    except Exception as e:
        return jsonify({"status": "❌ Failed", "error": str(e)})


if __name__ == '__main__':
    app.run(debug=True)
