from events import FillEvent, OrderEvent

class ExecutionHandler:
    """
    The ExecutionHandler abstract base class handles the interaction
    between a set of order objects and the actual market placement
    and receipt of fills for those orders.
    """
    def execute_order(self, event):
        raise NotImplementedError("Should implement execute_order()")

class SimulatedExecutionHandler(ExecutionHandler):
    """
    The SimulatedExecutionHandler simply converts all OrderEvents into
    FillEvents, with a commission of zero.

    This is used for backtesting purposes.
    """
    def __init__(self, events):
        self.events = events

    def execute_order(self, event):
        """
        Converts OrderEvents into FillEvents.
        """
        if event.type == 'ORDER':
            fill_event = FillEvent(
                timeindex="",  # This will be populated by the backtester
                symbol=event.symbol,
                exchange='ARCA',
                quantity=event.quantity,
                direction=event.direction,
                fill_cost=0.0, # This will be populated by the backtester
                commission=None
            )
            self.events.put(fill_event)
