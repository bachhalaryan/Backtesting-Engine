import datetime

from backtester import Backtester
from data_handler import CSVDataHandler
from portfolio import Portfolio
from execution_handler import SimulatedExecutionHandler
from strategy import BuyAndHoldStrategy, StressTestStrategy

if __name__ == "__main__":
    # Example usage:
    csv_dir = "./data"  # Assuming your CSV data is in a 'data' folder
    symbol_list = ["STRESSTEST"] # Example symbol
    initial_capital = 100000.0
    start_date = datetime.datetime(2023, 1, 1) # Example start date
    heartbeat = 0.0 # Not used in this simulated backtester

    backtester = Backtester(
        csv_dir,
        symbol_list,
        initial_capital,
        start_date,
        heartbeat,
        CSVDataHandler,
        SimulatedExecutionHandler,
        Portfolio,
        StressTestStrategy
    )
    backtester.simulate_trading()
