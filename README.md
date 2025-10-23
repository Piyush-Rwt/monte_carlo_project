# Monte Carlo Risk Simulation

This is a Flask web application that performs Monte Carlo simulations for stock prices and inventory management.

## Features

- **Stock Simulation:** Simulates future stock prices based on initial price, volatility, and time.
- **Inventory Simulation:** Simulates inventory levels based on demand, volatility, and lead time.
- **Admin Panel:** View and manage simulation results.

## Setup

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd monte-carlo-project
   ```

2. **Create a virtual environment and activate it:**
   ```bash
   python -m venv venv
   venv\Scripts\activate  # On Windows
   # source venv/bin/activate  # On macOS/Linux
   ```

3. **Install the dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up the database:**
   - Make sure you have a MySQL server running.
   - Create a database named `monte_carlo_database`.
   - Run the `database.sql` script to create the necessary tables.

5. **Configure the environment variables:**
   - Create a `.env` file in the root directory.
   - Copy the contents of `.env.example` into `.env` and update the values for your local environment.

## Running the Application

```bash
flask run
```

The application will be available at `http://127.0.0.1:5000`.

## Admin Panel

- Access the admin panel at `/admin`.
- The default password is `secure_admin_password` (you can change this in the `.env` file).
