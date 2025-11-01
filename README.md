# Monte Carlo Risk Simulation

This is a Flask web application that performs Monte Carlo simulations for stock prices and inventory management, configured for deployment on Render.

## Features

- **Stock Simulation:** Simulates future stock prices based on initial price, volatility, and time.
- **Inventory Simulation:** Simulates inventory levels based on demand, volatility, and lead time.
- **Admin Panel:** View and manage simulation results, protected by a password.

---

## Local Development Setup

1.  **Clone the repository:**
    '''bash
    git clone <repository-url>
    cd monte-carlo-project
    '''

2.  **Create a virtual environment and activate it:**
    '''bash
    python -m venv venv
    venv\Scripts\activate  # On Windows
    # source venv/bin/activate  # On macOS/Linux
    '''

3.  **Install the dependencies:**
    '''bash
    pip install -r requirements.txt
    '''

4.  **Set up the database:**
    - This application is configured to use PostgreSQL.
    - For local development, you can use a local PostgreSQL instance or a free one from a cloud provider.

5.  **Configure the environment variables:**
    - Create a file named `.env` in the root directory.
    - Add the following variables to the `.env` file:
      '''
      # A secret key for Flask sessions
      SECRET_KEY='your_super_secret_key'

      # The connection string for your local PostgreSQL database
      DATABASE_URL='postgresql://user:password@host:port/dbname'

      # The password for the /admin login page
      ADMIN_PASSWORD='your_admin_password'
      '''

6.  **Run the application:**
    '''bash
    flask run
    '''
    The application will be available at `http://127.0.0.1:5000`.

---

## Deployment on Render

This application is ready to be deployed on Render.

1.  **Push to GitHub:** Make sure your project is in a GitHub repository.

2.  **Create a Database on Render:**
    - In the Render dashboard, create a new **PostgreSQL** database.
    - Choose the **Free** tier.
    - After creation, copy the **Internal Connection String**.

3.  **Create a Web Service on Render:**
    - In the Render dashboard, create a new **Web Service** and connect it to your GitHub repository.
    - Configure the following settings:
        - **Region:** Choose a region close to you.
        - **Build Command:** `pip install -r requirements.txt`
        - **Start Command:** `gunicorn app:app`

4.  **Set Environment Variables:**
    - In your Web Service settings on Render, go to the **Environment** tab.
    - Add the following environment variables:
        - `DATABASE_URL`: Paste the **Internal Connection String** from your Render PostgreSQL database.
        - `ADMIN_PASSWORD`: Set a secure password for your admin panel.
        - `SECRET_KEY`: Set a long, random string for Flask sessions.
        - `PYTHON_VERSION`: `3.11.4` (or your desired Python version)

5.  **Create Database Tables:**
    - Go to your PostgreSQL database page on Render and open the **Shell** tab.
    - Run the following SQL commands one by one to create your tables:
      '''sql
      CREATE TABLE stock_simulations (
          id SERIAL PRIMARY KEY,
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
      '''
      '''sql
      CREATE TABLE inventory_simulations (
          id SERIAL PRIMARY KEY,
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
      '''

6.  **Deploy:** Render will automatically deploy your application. Once it's live, you can access it at the URL provided by Render.