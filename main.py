import datetime
import logging
from backtester import Backtester
from data_handler import CSVDataHandler
from portfolio import Portfolio
from execution_handler import SimulatedExecutionHandler, FixedCommissionCalculator
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

    commission_calculator = FixedCommissionCalculator(rate_per_share=0.0, min_commission=0.0)

    # --- Example 1: Full backtest ---
    # backtester = Backtester(
    #     csv_dir,
    #     symbol_list,
    #     initial_capital,
    #     start_date,
    #     heartbeat,
    #     CSVDataHandler,
    #     SimulatedExecutionHandler,
    #     Portfolio,
    #     EmaRsiStrategy,
    #     strategy_params=strategy_params,
    #     commission_calculator=commission_calculator
    # )

    # --- Example 2: Backtest on last 1000 bars ---
    # backtester = Backtester(
    #     csv_dir,
    #     symbol_list,
    #     initial_capital,
    #     start_date,
    #     heartbeat,
    #     CSVDataHandler,
    #     SimulatedExecutionHandler,
    #     Portfolio,
    #     EmaRsiStrategy,
    #     strategy_params=strategy_params,
    #     commission_calculator=commission_calculator,
    #     bars_from_end=1000
    # )

    # --- Example 3: Backtest on a specific date range ---
    # --- Example 3: Backtest on a specific date range ---
    # backtester = Backtester(
    #     csv_dir,
    #     symbol_list,
    #     initial_capital,
    #     start_date,
    #     heartbeat,
    #     CSVDataHandler,
    #     SimulatedExecutionHandler,
    #     Portfolio,
    #     EmaRsiStrategy,
    #     strategy_params=strategy_params,
    #     commission_calculator=commission_calculator,
    #     start_date_filter=datetime.datetime(2021, 1, 1),
    #     end_date_filter=datetime.datetime(2021, 12, 31)
    # )

    # --- Example 4: Backtest with resampling (e.g., to 1 hour) ---
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
        strategy_params=strategy_params,
        commission_calculator=commission_calculator,
        resample_interval="1H" # Resample to 1 hour bars
    )
    backtester.simulate_trading(log_level=logging.ERROR)