
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
    def __init__(self, strategy_id, symbol, datetime, signal_type, strength,
                 sizing_type=None, sizing_value=None,
                 order_type='MKT', limit_price=None, stop_price=None, trail_price=None,
                 immediate_fill=False):
        self.type = 'SIGNAL'
        self.symbol = symbol
        self.datetime = datetime
        self.signal_type = signal_type  # "LONG", "SHORT", "EXIT"
        self.strength = strength
        self.sizing_type = sizing_type
        self.sizing_value = sizing_value
        self.order_type = order_type
        self.limit_price = limit_price
        self.stop_price = stop_price
        self.trail_price = trail_price
        self.immediate_fill = immediate_fill

class OrderEvent(Event):
    """
    Handles the event of sending an Order to an ExecutionHandler.
    """
    def __init__(self, symbol, order_type, quantity, direction, limit_price=None, stop_price=None, trail_price=None, immediate_fill=False):
        self.type = 'ORDER'
        self.symbol = symbol
        self.order_type = order_type
        self.quantity = quantity
        self.direction = direction
        self.limit_price = limit_price
        self.stop_price = stop_price
        self.trail_price = trail_price
        self.immediate_fill = immediate_fill
        self.filled_quantity = 0
        self.highest_price_seen = -float('inf')
        self.lowest_price_seen = float('inf')

class CancelOrderEvent(Event):
    """
    Handles the event of sending a CancelOrder to an ExecutionHandler.
    """
    def __init__(self, order_id):
        self.type = 'CANCEL_ORDER'
        self.order_id = order_id

class FillEvent(Event):
    """
    Encapsulates the notion of a Filled Order, as received from an
    ExecutionHandler.
    """
    def __init__(self, timeindex, symbol, exchange, quantity, 
                 direction, fill_cost, commission=None, order_id=None, partial_fill=False):
        self.type = 'FILL'
        self.timeindex = timeindex
        self.symbol = symbol
        self.exchange = exchange
        self.quantity = quantity
        self.direction = direction
        self.fill_cost = fill_cost
        self.order_id = order_id
        self.partial_fill = partial_fill

        if commission is None:
            self.commission = 0.0 # Default to 0 if not provided
        else:
            self.commission = commission
