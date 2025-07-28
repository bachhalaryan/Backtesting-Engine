import datetime
import logging
from backtester import Backtester
from data_handler import CSVDataHandler
from portfolio import Portfolio
from execution_handler import SimulatedExecutionHandler
from strategy import BuyAndHoldStrategy, StressTestStrategy
from strategies.ema_rsi_strategy import EmaRsiStrategy

if __name__ == "__main__":
    # Example usage:
    csv_dir = "./data"
    symbol_list = ["EURUSD"]
    initial_capital = 100000.0
    start_date = datetime.datetime(2020, 1, 1)
    heartbeat = 0.0

    strategy_params = {
        'short_window': 20,
        'long_window': 50,
        'rsi_window': 14,
        'rsi_threshold': 70
    }

    backtester = Backtester(
        csv_dir,
        symbol_list,
        initial_capital,
        start_date,
        heartbeat,
        CSVDataHandler,
        SimulatedExecutionHandler,
        Portfolio,
        EmaRsiStrategy,
        strategy_params=strategy_params
    )
    backtester.simulate_trading(log_level=logging.ERROR)
