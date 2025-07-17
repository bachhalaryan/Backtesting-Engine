import datetime
import queue
import os
import logging
from event_bus import EventBus

from data_handler import CSVDataHandler
from strategy import BuyAndHoldStrategy
from portfolio import Portfolio
from execution_handler import SimulatedExecutionHandler, FixedCommissionCalculator
from events import MarketEvent, SignalEvent, OrderEvent, FillEvent
from performance_analyzer import PerformanceAnalyzer
from backtest_manager import BacktestManager
from logging_config import setup_logging

logger = logging.getLogger(__name__)

class Backtester:
    """
    Enscapsulates the settings and components for carrying out
    an event-driven backtest.
    """
    def __init__(self, csv_dir, symbol_list, initial_capital, 
                 start_date, heartbeat, data_handler, 
                 execution_handler, portfolio, strategy):
        self.csv_dir = csv_dir
        self.symbol_list = symbol_list
        self.initial_capital = initial_capital
        self.start_date = start_date
        self.heartbeat = heartbeat
        self.data_handler_cls = data_handler
        self.execution_handler_cls = execution_handler
        self.portfolio_cls = portfolio
        self.strategy_cls = strategy

        self.events = EventBus()
        self.signals = 0
        self.orders = 0
        self.fills = 0
        self.num_strats = 1
        self.current_market_event = None

        self._generate_trading_instances()

    def _generate_trading_instances(self):
        """
        Generates the trading instance objects from their class types.
        """
        self.data_handler = self.data_handler_cls(self.events, 
                                                  self.csv_dir, 
                                                  self.symbol_list)
        self.portfolio = self.portfolio_cls(self.data_handler, 
                                           self.events, 
                                           self.start_date, 
                                           self.initial_capital)
        self.execution_handler = self.execution_handler_cls(self.events, self.data_handler, commission_calculator=FixedCommissionCalculator())
        self.strategy = self.strategy_cls(self.symbol_list[0], 
                                          self.events, 
                                          self.data_handler, 
                                          self.portfolio, 
                                          self.execution_handler)

    def _run_backtest(self):
        """
        Executes the backtest.
        """
        logger.info("Starting backtest...")
        i = 0
        while True:
            i += 1
            # Update the market bars
            if self.data_handler.continue_backtest:
                self.data_handler.update_bars()
            else:
                logger.info("End of data reached. Halting backtest.")
                break

            # Handle events
            while True:
                try:
                    event = self.events.get(False)
                except queue.Empty:
                    break
                else:
                    if event is not None:
                        try:
                            if event.type == 'MARKET':
                                self.current_market_event = event
                                self.execution_handler.update(event)
                                self.strategy.calculate_signals(event)
                                self.portfolio.update_timeindex(event)
                            elif event.type == 'SIGNAL':
                                self.signals += 1
                                self.portfolio.update_signal(event)
                            elif event.type == 'ORDER':
                                self.orders += 1
                                self.execution_handler.execute_order(event)
                                if event.immediate_fill and self.current_market_event:
                                    self.execution_handler.process_immediate_order(event.order_id, self.current_market_event)
                            elif event.type == 'FILL':
                                self.fills += 1
                                self.portfolio.update_fill(event)
                            elif event.type == 'CANCEL_ORDER':
                                self.execution_handler.execute_order(event)
                        except Exception as e:
                            logger.error(f"Error processing event {event.type}: {e}", exc_info=True)

    def simulate_trading(self):
        """
        Simulates the backtest and outputs portfolio performance.
        """
        setup_logging()
        self._run_backtest()
        self.portfolio.create_equity_curve_dataframe()

        # --- Performance Analysis and Reporting ---
        logger.info("Calculating performance metrics...")
        performance_analyzer = PerformanceAnalyzer(self.portfolio, self.data_handler)
        metrics = performance_analyzer.calculate_metrics()

        # Define backtest name and parameters for saving
        backtest_name = f"backtest_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}"
        backtest_params = {
            "initial_capital": self.initial_capital,
            "start_date": str(self.start_date),
            "symbol_list": self.symbol_list,
            "data_handler": self.data_handler_cls.__name__,
            "strategy": self.strategy_cls.__name__,
            "execution_handler": self.execution_handler_cls.__name__
        }

        # Initialize BacktestManager to get the base directory
        backtest_manager = BacktestManager()
        
        # Define the specific directory for this backtest run
        backtest_run_dir = backtest_manager._get_backtest_path(backtest_name)
        os.makedirs(backtest_run_dir, exist_ok=True) # Ensure the directory exists before saving plots

        # Generate plot file paths within the backtest_run_dir
        plot_filepaths = {
            "equity_curve_matplotlib": os.path.join(backtest_run_dir, "equity_curve.png"),
            "drawdown_matplotlib": os.path.join(backtest_run_dir, "drawdown.png"),
            "equity_curve_plotly": os.path.join(backtest_run_dir, "equity_curve.html"),
            "drawdown_plotly": os.path.join(backtest_run_dir, "drawdown.html"),
            "trades_plotly": os.path.join(backtest_run_dir, "trades.html")
        }

        # Generate plots directly into the backtest_run_dir
        logger.info("Generating performance plots...")
        performance_analyzer.generate_equity_curve_matplotlib(plot_filepaths["equity_curve_matplotlib"])
        performance_analyzer.generate_drawdown_matplotlib(plot_filepaths["drawdown_matplotlib"])
        performance_analyzer.generate_equity_curve_plotly(plot_filepaths["equity_curve_plotly"])
        performance_analyzer.generate_drawdown_plotly(plot_filepaths["drawdown_plotly"])
        performance_analyzer.generate_trades_plotly(plot_filepaths["trades_plotly"])

        # Save backtest results (plots are already in place)
        logger.info("Saving backtest results...")
        backtest_manager.save_backtest(
            backtest_name,
            self.portfolio,
            backtest_params,
            metrics,
            plot_filepaths # Pass the paths for recording, not for moving
        )

        logger.info("--- Backtest Summary ---")
        for key, value in metrics.items():
            logger.info(f"{key}: {value:.2f}")
        logger.info("------------------------")
        logger.info(f"Detailed results saved to: {backtest_manager.base_dir}/{backtest_name}")
