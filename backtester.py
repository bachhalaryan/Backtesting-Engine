import datetime
import queue

from data_handler import CSVDataHandler
from strategy import BuyAndHoldStrategy
from portfolio import Portfolio
from execution_handler import SimulatedExecutionHandler
from events import MarketEvent, SignalEvent, OrderEvent, FillEvent

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

        self.events = queue.Queue()
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
        self.strategy = self.strategy_cls(self.symbol_list[0], 
                                          self.events)
        self.portfolio = self.portfolio_cls(self.data_handler, 
                                           self.events, 
                                           self.start_date, 
                                           self.initial_capital)
        self.execution_handler = self.execution_handler_cls(self.events, self.data_handler)

    def _run_backtest(self):
        """
        Executes the backtest.
        """
        i = 0
        while True:
            i += 1
            # Update the market bars
            if self.data_handler.continue_backtest:
                self.data_handler.update_bars()
            else:
                break

            # Handle events
            while True:
                try:
                    event = self.events.get(False)
                except queue.Empty:
                    break
                else:
                    if event is not None:
                        if event.type == 'MARKET':
                            self.current_market_event = event
                            self.strategy.calculate_signals(event)
                            self.portfolio.update_timeindex(event)
                            self.execution_handler.update(event)
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

    def simulate_trading(self):
        """
        Simulates the backtest and outputs portfolio performance.
        """
        self._run_backtest()
        self.portfolio.create_equity_curve_dataframe()
        print(self.portfolio.equity_curve.tail(10))
