```python
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
#     resample_interval="1H" # Resample to 1 hour bars
# )
```