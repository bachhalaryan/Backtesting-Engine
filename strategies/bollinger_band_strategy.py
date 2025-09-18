import pandas as pd
from ta.volatility import BollingerBands
from strategy import Strategy
from events import SignalEvent

class BollingerBandStrategy(Strategy):
    """
    A mean-reversion strategy using Bollinger Bands.
    """
    def __init__(self, symbol, events, data_handler, portfolio, execution_handler, bb_window=20, bb_std_dev=2):
        self.symbol = symbol
        self.events = events
        self.data_handler = data_handler
        self.portfolio = portfolio
        self.execution_handler = execution_handler
        self.bb_window = bb_window
        self.bb_std_dev = bb_std_dev
        self.bought = self._calculate_initial_bought()

    def _calculate_initial_bought(self):
        if self.portfolio.current_positions.get(self.symbol, 0) > 0:
            return 'LONG'
        elif self.portfolio.current_positions.get(self.symbol, 0) < 0:
            return 'SHORT'
        else:
            return 'OUT'

    def calculate_signals(self, event):
        """
        Generates trading signals based on Bollinger Bands.
        """
        if event.type == 'MARKET':
            bars = self.data_handler.get_bars(self.symbol, N=self.bb_window)
            if bars is not None and not bars.empty and len(bars) >= self.bb_window:
                close_prices = bars['close']
                
                # Initialize BollingerBands indicator
                indicator_bb = BollingerBands(close=close_prices, window=self.bb_window, window_dev=self.bb_std_dev)

                # Get latest values
                upper_band = indicator_bb.bollinger_hband().iloc[-1]
                lower_band = indicator_bb.bollinger_lband().iloc[-1]
                middle_band = indicator_bb.bollinger_mavg().iloc[-1]
                latest_close = close_prices.iloc[-1]

                if self.bought == 'OUT':
                    if latest_close < lower_band:
                        signal = SignalEvent(1, self.symbol, event.timeindex, 'LONG', 1.0, sizing_type='FIXED_SHARES', sizing_value=1, order_type='MKT')
                        self.events.put(signal)
                        self.bought = 'LONG'
                    elif latest_close > upper_band:
                        signal = SignalEvent(1, self.symbol, event.timeindex, 'SHORT', 1.0, sizing_type='FIXED_SHARES', sizing_value=1, order_type='MKT')
                        self.events.put(signal)
                        self.bought = 'SHORT'

                elif self.bought == 'LONG':
                    if latest_close >= middle_band:
                        signal = SignalEvent(1, self.symbol, event.timeindex, 'EXIT', 1.0, sizing_type='FIXED_SHARES', sizing_value=abs(self.portfolio.current_positions.get(self.symbol, 0)), order_type='MKT')
                        self.events.put(signal)
                        self.bought = 'OUT'
                
                elif self.bought == 'SHORT':
                    if latest_close <= middle_band:
                        signal = SignalEvent(1, self.symbol, event.timeindex, 'EXIT', 1.0, sizing_type='FIXED_SHARES', sizing_value=abs(self.portfolio.current_positions.get(self.symbol, 0)), order_type='MKT')
                        self.events.put(signal)
                        self.bought = 'OUT'
