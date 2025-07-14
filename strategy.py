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
    def __init__(self, symbol, events, data_handler, portfolio, execution_handler):
        self.symbol = symbol
        self.events = events
        self.data_handler = data_handler # Store data_handler for historical data access
        self.portfolio = portfolio
        self.execution_handler = execution_handler
        self.bought = False
        self.bar_count = 0

    def calculate_signals(self, event):
        """
        For this strategy, we will demonstrate various order types.
        """
        if event.type == 'MARKET':
            self.bar_count += 1
            
            # Demonstrate accessing historical data
            historical_bars = self.data_handler.get_historical_bars(self.symbol, N=3)
            if not historical_bars.empty:
                print(f"Strategy: Latest 3 historical bars for {self.symbol}:\n{historical_bars}")

            # Demonstrate accessing portfolio and execution handler state
            print(f"Strategy: Current cash: {self.portfolio.current_holdings['cash']:.2f}")
            print(f"Strategy: Current {self.symbol} position: {self.portfolio.current_positions[self.symbol]}")
            print(f"Strategy: Open orders: {len(self.execution_handler.orders)}")

            current_price = self.data_handler.get_latest_bars(self.symbol)[0][1]['close']

            if not self.bought and self.bar_count == 1:
                # Initial Market Buy Order
                print("Strategy: Placing initial Market BUY order.")
                signal = SignalEvent(1, self.symbol, event.timeindex, 'LONG', 1.0,
                                     sizing_type='FIXED_SHARES', sizing_value=100,
                                     order_type='MKT', immediate_fill=False)
                self.events.put(signal)
                self.bought = True

            elif self.bought and self.bar_count == 3:
                # Limit Buy Order (buy if price drops)
                limit_price = current_price * 0.95 # 5% below current price
                print(f"Strategy: Placing Limit BUY order at {limit_price:.2f}.")
                signal = SignalEvent(1, self.symbol, event.timeindex, 'LONG', 1.0,
                                     sizing_type='FIXED_SHARES', sizing_value=50,
                                     order_type='LMT', limit_price=limit_price)
                self.events.put(signal)

            elif self.bought and self.bar_count == 5:
                # Stop Sell Order (sell if price rises significantly)
                stop_price = current_price * 1.05 # 5% above current price
                print(f"Strategy: Placing Stop SELL order at {stop_price:.2f}.")
                signal = SignalEvent(1, self.symbol, event.timeindex, 'EXIT', 1.0,
                                     sizing_type='FIXED_SHARES', sizing_value=self.portfolio.current_positions[self.symbol],
                                     order_type='STP', stop_price=stop_price)
                self.events.put(signal)

            elif self.bought and self.bar_count == 7:
                # Trailing Stop Sell Order
                trail_price_offset = current_price * 0.02 # 2% trailing stop
                print(f"Strategy: Placing Trailing Stop SELL order with offset {trail_price_offset:.2f}.")
                signal = SignalEvent(1, self.symbol, event.timeindex, 'EXIT', 1.0,
                                     sizing_type='FIXED_SHARES', sizing_value=self.portfolio.current_positions[self.symbol],
                                     order_type='TRAIL', trail_price=trail_price_offset)
                self.events.put(signal)

            elif self.bought and self.bar_count == 9:
                # Immediate Fill Market Buy Order (for demonstration of immediate_fill)
                print("Strategy: Placing Immediate Fill Market BUY order.")
                signal = SignalEvent(1, self.symbol, event.timeindex, 'LONG', 1.0,
                                     sizing_type='FIXED_SHARES', sizing_value=20,
                                     order_type='MKT', immediate_fill=True)
                self.events.put(signal)

            elif self.bought and self.bar_count == 10:
                # Final Exit Market Order
                print("Strategy: Placing final Market EXIT order.")
                signal = SignalEvent(1, self.symbol, event.timeindex, 'EXIT', 1.0,
                                     sizing_type='FIXED_SHARES', sizing_value=self.portfolio.current_positions[self.symbol],
                                     order_type='MKT', immediate_fill=False)
                self.events.put(signal)
                self.bought = False # Reset for potential re-entry if backtest continues
