
class Event:
    """
    Base class for all events in the backtesting engine.
    """
    pass

class MarketEvent(Event):
    """
    Handles the event of receiving a new market update (e.g., a new bar).
    """
    def __init__(self, timeindex):
        self.type = 'MARKET'
        self.timeindex = timeindex

class SignalEvent(Event):
    """
    Handles the event of sending a Signal from a Strategy object.
    This is received by a Portfolio object and acted upon.
    """
    def __init__(self, strategy_id, symbol, datetime, signal_type, strength):
        self.type = 'SIGNAL'
        self.symbol = symbol
        self.datetime = datetime
        self.signal_type = signal_type  # "LONG", "SHORT", "EXIT"
        self.strength = strength

class OrderEvent(Event):
    """
    Handles the event of sending an Order to an ExecutionHandler.
    """
    def __init__(self, symbol, order_type, quantity, direction):
        self.type = 'ORDER'
        self.symbol = symbol
        self.order_type = order_type  # "MKT" or "LMT"
        self.quantity = quantity
        self.direction = direction  # "BUY" or "SELL"

class FillEvent(Event):
    """
    Encapsulates the notion of a Filled Order, as received from an
    ExecutionHandler.
    """
    def __init__(self, timeindex, symbol, exchange, quantity, 
                 direction, fill_cost, commission=None):
        self.type = 'FILL'
        self.timeindex = timeindex
        self.symbol = symbol
        self.exchange = exchange
        self.quantity = quantity
        self.direction = direction
        self.fill_cost = fill_cost

        # Calculate commission if not provided
        if commission is None:
            self.commission = self.calculate_commission()
        else:
            self.commission = commission

    def calculate_commission(self):
        """
        Calculates the commission for the fill.
        """
        # Example: Interactive Brokers-style commission
        # $0.0035 per share, min $0.35, max 1% of trade value
        full_cost = 0.0035 * self.quantity
        if full_cost < 0.35:
            full_cost = 0.35
        return full_cost
