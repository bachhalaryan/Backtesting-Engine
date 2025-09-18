import datetime
import logging
from backtester import Backtester
from data_handler import CSVDataHandler
from portfolio import Portfolio
from execution_handler import SimulatedExecutionHandler, FixedCommissionCalculator
from strategies.bollinger_band_strategy import BollingerBandStrategy
# from strategies.midbar import Midbar

if __name__ == "__main__":
    # Example usage:
    csv_dir = "./data"
    symbol_list = ["EURUSD"]
    initial_capital = 100000.0
    start_date = datetime.datetime(2020, 1, 1)
    heartbeat = 0.0

    strategy_params = {"bb_window": 20, "bb_std_dev": 2}

    commission_calculator = FixedCommissionCalculator(
        rate_per_share=0.0, min_commission=0.0
    )

    backtester = Backtester(
        csv_dir,
        ["EURUSD"],
        initial_capital,
        start_date,
        heartbeat,
        CSVDataHandler,
        SimulatedExecutionHandler,
        Portfolio,
        BollingerBandStrategy,
        strategy_params=strategy_params,
        commission_calculator=commission_calculator,
        bars_from_end=10000,
    )
    backtester.simulate_trading(log_level=logging.INFO)
