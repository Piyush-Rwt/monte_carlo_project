Monte Carlo Stock Price Simulator

This project is a web-based application that simulates future stock prices using the Monte Carlo method.

What we have done today

Set up a new project structure with a Flask backend and a web interface (HTML, CSS, JS).

Created a Python backend with Flask to perform the Monte Carlo simulation.

Developed an interactive interface using HTML, CSS, and JavaScript.

Established communication between the frontend and backend using a JSON API.

Integrated MySQL to store simulation results for both stock and inventory simulations.

The application is now fully functional and can be run locally.

Algorithms Used

Monte Carlo Simulation: Generates multiple random paths of future stock prices based on daily volatility and randomness.

Statistical Analysis: Calculates average final price, best and worst-case prices, probability of reaching a target, probability of loss, 90% confidence intervals, and Value at Risk.

Inventory Simulation (Supply Chain): Uses random daily demand and lead time to simulate stock levels and probability of stockouts.

Data Structures

NumPy Arrays: Efficiently store and process simulation paths.

Pandas DataFrames: Used for analysis and manipulation of results.

JSON: For frontend-backend communication.

MySQL Tables:

stock_simulations: Stores all stock simulation runs (initial price, volatility, days, simulations, target price, statistics).

inventory_simulations: Stores all inventory simulation runs (initial stock, daily demand, volatility, lead time, statistics).

Libraries Used
Backend (Python)

Flask: Micro web framework for backend API.

NumPy: Numerical computing for Monte Carlo simulation.

Pandas: Data analysis and manipulation.

mysql-connector-python: Connects Python backend to MySQL database.

Frontend (JavaScript)

Chart.js: Creates interactive charts and graphs.

Why We Store Data

Keep a record of all simulation runs.

Analyze results later for trends or decision-making.

Allow multiple users to run simulations without losing data.

Enable future machine learning or risk-analysis enhancements.

Workflow

User inputs simulation parameters in the interface.

Backend (Python + Flask) runs the Monte Carlo simulation or inventory simulation.

Simulation results are saved in the MySQL database.

Charts and statistical summaries are displayed in the web interface.

Admin panel can view or delete stored results as needed.

How to Run

Install dependencies : Open a terminal in the project directory and run:

pip install -r requirements.txt


Run the backend:

python app.py


Open in browser: Go to http://127.0.0.1:5000.


FILE STRUCTURE
monte_carlo_project/
├── static/
│   ├── css/
│   │   ├── simulate.css
│   │   └── style.css
│   └── js/
│       ├── inventory.js
│       ├── main.js
│       ├── script.js
│       └── simulate.js
├── templates/
│   ├── admin_dashboard.html
│   ├── admin_login.html
│   ├── index.html
│   ├── inventory.html
│   ├── simulate.html
│   └── stock_simulation.html
├── app.py
├── README.md
└── requirements.txt