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
    The simulated execution handler should be connected to a data handler.
    This is to ensure that it has access to the latest bars and can
    appropriately simulate the fill of orders.
    """
    def __init__(self, events, bars, slippage_bps=0, partial_fill_volume_pct=1.0):
        self.events = events
        self.bars = bars
        self.orders = {}
        self.order_id = 0
        self.slippage_bps = slippage_bps
        self.partial_fill_volume_pct = partial_fill_volume_pct

    def _apply_slippage(self, price, direction):
        if self.slippage_bps == 0:
            return price
        
        slippage_amount = price * (self.slippage_bps / 10000.0)
        if direction == 'BUY':
            return price * (1 + self.slippage_bps / 10000.0)
        elif direction == 'SELL':
            return price * (1 - self.slippage_bps / 10000.0)
        return price

    def execute_order(self, event):
        """
        Simulates the execution of an order.
        """
        if event.type == 'ORDER':
            self.order_id += 1
            event.order_id = self.order_id # Assign order_id to the event
            self.orders[self.order_id] = event

        elif event.type == 'CANCEL_ORDER':
            if event.order_id in self.orders:
                del self.orders[event.order_id]

    def process_immediate_order(self, order_id, market_event):
        """
        Processes a single order immediately using the provided market data.
        This is used for "cheat" orders that need to be filled within the
        same market bar they are generated.
        """
        if order_id in self.orders:
            order = self.orders[order_id]
            bar = self.bars.get_latest_bars(order.symbol)[0] # Use the latest bar from data handler
            
            # Update highest/lowest price seen for trailing stops if applicable
            if order.order_type == 'TRAIL':
                order.highest_price_seen = max(order.highest_price_seen, bar[1]['high'])
                order.lowest_price_seen = min(order.lowest_price_seen, bar[1]['low'])

            remaining_quantity = order.quantity - order.filled_quantity
            if remaining_quantity <= 0:
                del self.orders[order_id]
                return

            fill_event = self._check_order(order_id, order, remaining_quantity)
            if fill_event:
                self.events.put(fill_event)
                order.filled_quantity += fill_event.quantity
                if order.filled_quantity >= order.quantity:
                    del self.orders[order_id]

    def update(self, event):
        """
        Updates the execution handler with the latest market data.
        """
        if event.type == 'MARKET':
            for order_id, order in list(self.orders.items()):
                
                # Update highest/lowest price seen for trailing stops
                bar = self.bars.get_latest_bars(order.symbol)[0]
                if order.order_type == 'TRAIL':
                    order.highest_price_seen = max(order.highest_price_seen, bar[1]['high'])
                    order.lowest_price_seen = min(order.lowest_price_seen, bar[1]['low'])

                # Calculate remaining quantity
                remaining_quantity = order.quantity - order.filled_quantity
                if remaining_quantity <= 0:
                    del self.orders[order_id]
                    continue

                fill_event = self._check_order(order_id, order, remaining_quantity)
                if fill_event:
                    self.events.put(fill_event)
                    order.filled_quantity += fill_event.quantity
                    if order.filled_quantity >= order.quantity:
                        del self.orders[order_id]

    def _check_order(self, order_id, order, remaining_quantity):
        """
        Checks if an order has been filled.
        """
        bar = self.bars.get_latest_bars(order.symbol)[0]
        if order.order_type == 'MKT':
            return self._fill_market_order(order_id, order, bar, remaining_quantity)
        elif order.order_type == 'LMT':
            return self._fill_limit_order(order_id, order, bar, remaining_quantity)
        elif order.order_type == 'STP':
            return self._fill_stop_order(order_id, order, bar, remaining_quantity)
        elif order.order_type == 'STP_LMT':
            return self._fill_stop_limit_order(order_id, order, bar, remaining_quantity)
        elif order.order_type == 'TRAIL':
            return self._fill_trailing_stop_order(order_id, order, bar, remaining_quantity)
        return None

    def _fill_market_order(self, order_id, order, bar, remaining_quantity):
        """
        Fills a market order.
        """
        fill_price = bar[1]['open']
        fill_price = self._apply_slippage(fill_price, order.direction)

        max_fill_quantity = int(bar[1]['volume'] * self.partial_fill_volume_pct)
        fill_quantity = min(remaining_quantity, max_fill_quantity)
        partial_fill = fill_quantity < remaining_quantity

        fill_cost = fill_price * fill_quantity
        return FillEvent(bar[0], order.symbol, 'ARCA', fill_quantity, order.direction, fill_cost, order_id=order_id, partial_fill=partial_fill)

    def _fill_limit_order(self, order_id, order, bar, remaining_quantity):
        """
        Fills a limit order.
        """
        max_fill_quantity = int(bar[1]['volume'] * self.partial_fill_volume_pct)

        if order.direction == 'BUY':
            if bar[1]['low'] <= order.limit_price:
                fill_price = min(bar[1]['open'], order.limit_price)
                fill_price = self._apply_slippage(fill_price, order.direction)
                fill_quantity = min(remaining_quantity, max_fill_quantity)
                partial_fill = fill_quantity < remaining_quantity
                fill_cost = fill_price * fill_quantity
                return FillEvent(bar[0], order.symbol, 'ARCA', fill_quantity, order.direction, fill_cost, order_id=order_id, partial_fill=partial_fill)
        elif order.direction == 'SELL':
            if bar[1]['open'] >= order.limit_price:
                fill_price = bar[1]['open']
                fill_price = self._apply_slippage(fill_price, order.direction)
                fill_quantity = min(remaining_quantity, max_fill_quantity)
                partial_fill = fill_quantity < remaining_quantity
                fill_cost = fill_price * fill_quantity
                return FillEvent(bar[0], order.symbol, 'ARCA', fill_quantity, order.direction, fill_cost, order_id=order_id, partial_fill=partial_fill)
            elif bar[1]['high'] >= order.limit_price:
                fill_price = order.limit_price
                fill_price = self._apply_slippage(fill_price, order.direction)
                fill_quantity = min(remaining_quantity, max_fill_quantity)
                partial_fill = fill_quantity < remaining_quantity
                fill_cost = fill_price * fill_quantity
                return FillEvent(bar[0], order.symbol, 'ARCA', fill_quantity, order.direction, fill_cost, order_id=order_id, partial_fill=partial_fill)
        return None

    def _fill_stop_order(self, order_id, order, bar, remaining_quantity):
        """
        Fills a stop order.
        """
        max_fill_quantity = int(bar[1]['volume'] * self.partial_fill_volume_pct)

        if order.direction == 'BUY':
            if bar[1]['high'] >= order.stop_price:
                fill_price = order.stop_price
                if bar[1]['open'] >= order.stop_price:
                    fill_price = bar[1]['open']
                if bar[1]['high'] >= order.stop_price and bar[1]['open'] < order.stop_price:
                    fill_price = bar[1]['high'] # Cheat on high
                fill_price = self._apply_slippage(fill_price, order.direction)
                fill_quantity = min(remaining_quantity, max_fill_quantity)
                partial_fill = fill_quantity < remaining_quantity
                fill_cost = fill_price * fill_quantity
                return FillEvent(bar[0], order.symbol, 'ARCA', fill_quantity, order.direction, fill_cost, order_id=order_id, partial_fill=partial_fill)
        elif order.direction == 'SELL':
            if bar[1]['low'] <= order.stop_price:
                fill_price = order.stop_price
                if bar[1]['open'] <= order.stop_price:
                    fill_price = bar[1]['open']
                if bar[1]['low'] <= order.stop_price and bar[1]['open'] > order.stop_price:
                    fill_price = bar[1]['low'] # Cheat on low
                fill_price = self._apply_slippage(fill_price, order.direction)
                fill_quantity = min(remaining_quantity, max_fill_quantity)
                partial_fill = fill_quantity < remaining_quantity
                fill_cost = fill_price * fill_quantity
                return FillEvent(bar[0], order.symbol, 'ARCA', fill_quantity, order.direction, fill_cost, order_id=order_id, partial_fill=partial_fill)
        return None

    def _fill_stop_limit_order(self, order_id, order, bar, remaining_quantity):
        """
        Fills a stop-limit order.
        """
        max_fill_quantity = int(bar[1]['volume'] * self.partial_fill_volume_pct)

        if order.direction == 'BUY':
            if bar[1]['high'] >= order.stop_price:
                # Stop triggered, now check limit condition
                if bar[1]['low'] <= order.limit_price:
                    fill_price = min(bar[1]['open'], order.limit_price)
                    fill_price = self._apply_slippage(fill_price, order.direction)
                    fill_quantity = min(remaining_quantity, max_fill_quantity)
                    partial_fill = fill_quantity < remaining_quantity
                    fill_cost = fill_price * fill_quantity
                    return FillEvent(bar[0], order.symbol, 'ARCA', fill_quantity, order.direction, fill_cost, order_id=order_id, partial_fill=partial_fill)
        elif order.direction == 'SELL':
            if bar[1]['low'] <= order.stop_price:
                # Stop triggered, now check limit condition
                if bar[1]['high'] >= order.limit_price:
                    fill_price = max(bar[1]['open'], order.limit_price)
                    fill_price = self._apply_slippage(fill_price, order.direction)
                    fill_quantity = min(remaining_quantity, max_fill_quantity)
                    partial_fill = fill_quantity < remaining_quantity
                    fill_cost = fill_price * fill_quantity
                    return FillEvent(bar[0], order.symbol, 'ARCA', fill_quantity, order.direction, fill_cost, order_id=order_id, partial_fill=partial_fill)
        return None

    def _fill_trailing_stop_order(self, order_id, order, bar, remaining_quantity):
        """
        Fills a trailing stop order.
        """
        max_fill_quantity = int(bar[1]['volume'] * self.partial_fill_volume_pct)

        if order.direction == 'BUY':
            # Update highest price seen
            order.highest_price_seen = max(order.highest_price_seen, bar[1]['high'])
            
            # Calculate trailing stop price
            trail_price = order.highest_price_seen - order.trail_price

            if bar[1]['low'] <= trail_price:
                fill_price = trail_price
                if bar[1]['open'] <= trail_price:
                    fill_price = bar[1]['open']
                fill_price = self._apply_slippage(fill_price, order.direction)
                fill_quantity = min(remaining_quantity, max_fill_quantity)
                partial_fill = fill_quantity < remaining_quantity
                fill_cost = fill_price * fill_quantity
                return FillEvent(bar[0], order.symbol, 'ARCA', fill_quantity, order.direction, fill_cost, order_id=order_id, partial_fill=partial_fill)
        elif order.direction == 'SELL':
            # Update lowest price seen
            order.lowest_price_seen = min(order.lowest_price_seen, bar[1]['low'])

            # Calculate trailing stop price
            trail_price = order.lowest_price_seen + order.trail_price

            if bar[1]['high'] >= trail_price:
                fill_price = trail_price
                if bar[1]['open'] >= trail_price:
                    fill_price = bar[1]['open']
                fill_price = self._apply_slippage(fill_price, order.direction)
                fill_quantity = min(remaining_quantity, max_fill_quantity)
                partial_fill = fill_quantity < remaining_quantity
                fill_cost = fill_price * fill_quantity
                return FillEvent(bar[0], order.symbol, 'ARCA', fill_quantity, order.direction, fill_cost, order_id=order_id, partial_fill=partial_fill)
        return None