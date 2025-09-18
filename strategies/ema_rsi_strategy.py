import pandas as pd
from ta.trend import EMAIndicator
from ta.momentum import RSIIndicator

from strategy import Strategy
from events import SignalEvent

class EmaRsiStrategy(Strategy):
    """
    A strategy that combines Exponential Moving Averages (EMAs) for trend following
    and the Relative Strength Index (RSI) for momentum filtering.
    """
    def __init__(self, symbol, events, data_handler, portfolio, execution_handler, short_window=20, long_window=50, rsi_window=14, rsi_threshold=70):
        self.symbol = symbol
        self.events = events
        self.data_handler = data_handler
        self.portfolio = portfolio
        self.execution_handler = execution_handler
        self.short_window = short_window
        self.long_window = long_window
        self.rsi_window = rsi_window
        self.rsi_threshold = rsi_threshold
        self.bought = self._calculate_initial_bought()

    def _calculate_initial_bought(self):
        if self.portfolio.current_positions[self.symbol] > 0:
            return 'LONG'
        elif self.portfolio.current_positions[self.symbol] < 0:
            return 'SHORT'
        else:
            return 'OUT'

    def calculate_signals(self, event):
        """
        Generates trading signals based on EMA crossover and RSI filter.
        """
        if event.type == 'MARKET':
            bars = self.data_handler.get_bars(self.symbol, N=self.long_window)
            if bars is not None and not bars.empty and len(bars) >= self.long_window:
                close_prices = bars['close']

                short_ema = EMAIndicator(close=close_prices, window=self.short_window).ema_indicator().iloc[-1]
                long_ema = EMAIndicator(close=close_prices, window=self.long_window).ema_indicator().iloc[-1]
                rsi = RSIIndicator(close=close_prices, window=self.rsi_window).rsi().iloc[-1]

                if self.bought == 'OUT':
                    if short_ema > long_ema and rsi < self.rsi_threshold:
                        signal = SignalEvent(1, self.symbol, event.timeindex, 'LONG', 1.0, sizing_type='FIXED_SHARES', sizing_value=1, order_type='MKT')
                        self.events.put(signal)
                        self.bought = 'LONG'

                elif self.bought == 'LONG':
                    if short_ema < long_ema:
                        signal = SignalEvent(1, self.symbol, event.timeindex, 'EXIT', 1.0, sizing_type='FIXED_SHARES', sizing_value=abs(self.portfolio.current_positions[self.symbol]), order_type='MKT')
                        self.events.put(signal)
                        self.bought = 'OUT'