from events import SignalEvent

class Strategy:
    """
    Strategy is an abstract base class providing an interface for
    all subsequent (inherited) strategy handling objects.

    The goal of a Strategy object is to generate SignalEvents, which
    are subsequently used by the Portfolio object to generate the
    appropriate OrderEvents.
    """
    def calculate_signals(self, event):
        raise NotImplementedError("Should implement calculate_signals()")

class BuyAndHoldStrategy(Strategy):
    """
    A testing strategy that simply purchases a fixed quantity of a
    security and holds it until a specified date passes.
    """
    def __init__(self, symbol, events, data_handler):
        self.symbol = symbol
        self.events = events
        self.data_handler = data_handler # Store data_handler for historical data access
        self.bought = False
        self.bar_count = 0

    def calculate_signals(self, event):
        """
        For this strategy, we will simply buy 100 units of the
        first symbol we receive and then sell after 5 bars.
        Also, demonstrate access to historical data.
        """
        if event.type == 'MARKET':
            self.bar_count += 1
            
            # Demonstrate accessing historical data
            # Get the last 3 bars for the symbol
            historical_bars = self.data_handler.get_historical_bars(self.symbol, N=3)
            if not historical_bars.empty:
                print(f"Strategy: Latest 3 historical bars for {self.symbol}:\n{historical_bars}")

            if not self.bought:
                signal = SignalEvent(1, self.symbol, event.timeindex, 'LONG', 1.0)
                self.events.put(signal)
                self.bought = True
            elif self.bought and self.bar_count == 5:
                signal = SignalEvent(1, self.symbol, event.timeindex, 'EXIT', 1.0)
                self.events.put(signal)
                self.bought = False # Reset for potential re-entry if backtest continues
