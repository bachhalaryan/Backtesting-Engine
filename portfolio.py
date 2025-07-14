from events import OrderEvent
import pandas as pd

class Portfolio:
    """
    The Portfolio is designed to hold the current positions and cash
    values of a trading account. It also provides methods to calculate
    the total portfolio value and generate OrderEvents from SignalEvents.
    """
    def __init__(self, bars, events, start_date, initial_capital=100000.0):
        self.bars = bars
        self.events = events
        self.symbol_list = self.bars.symbol_list
        self.start_date = start_date
        self.initial_capital = initial_capital

        self.all_positions = self._construct_all_positions()
        self.current_positions = dict((k, v) for k, v in [(s, 0) for s in self.symbol_list])

        self.all_holdings = self._construct_all_holdings()
        self.current_holdings = self._construct_current_holdings()
        self.equity_curve = pd.DataFrame()

    def create_equity_curve_dataframe(self):
        self.equity_curve = pd.DataFrame(self.all_holdings)
        self.equity_curve.set_index("datetime", inplace=True)
        self.equity_curve["returns"] = self.equity_curve["total"].pct_change()
        self.equity_curve["equity_curve"] = (1 + self.equity_curve["returns"]).cumprod()
        self.equity_curve["equity_curve"] = self.equity_curve["equity_curve"] * self.initial_capital

    def _construct_all_positions(self):
        """
        Constructs the positions list using the start_date to ensure
        that a historical record of the portfolio is kept.
        """
        d = dict((k, v) for k, v in [(s, 0) for s in self.symbol_list])
        d['datetime'] = self.start_date
        return [d]

    def _construct_all_holdings(self):
        """
        Constructs the holdings list using the start_date to ensure
        that a historical record of the portfolio is kept.
        """
        d = dict((k, v) for k, v in [(s, 0.0) for s in self.symbol_list])
        d['datetime'] = self.start_date
        d['cash'] = self.initial_capital
        d['commission'] = 0.0
        d['total'] = self.initial_capital
        return [d]

    def _construct_current_holdings(self):
        """
        Constructs the dictionary which will hold the instantaneous
        value of the portfolio at the current time_index.
        """
        d = dict((k, v) for k, v in [(s, 0.0) for s in self.symbol_list])
        d['cash'] = self.initial_capital
        d['commission'] = 0.0
        d['total'] = self.initial_capital
        return d

    def update_timeindex(self, event):
        """
        Adds a new record to the positions matrix for the current
        market data bar. This reflects the PREVIOUS bar's holdings
        prior to any new orders being executed.
        """
        latest_datetime = self.bars.get_latest_bars(self.symbol_list[0])[0][0]

        # Update positions
        dp = dict((k, v) for k, v in [(s, 0) for s in self.symbol_list])
        dp['datetime'] = latest_datetime
        for s in self.symbol_list:
            dp[s] = self.current_positions[s]
        self.all_positions.append(dp)

        # Update holdings
        dh = dict((k, v) for k, v in [(s, 0.0) for s in self.symbol_list])
        dh['datetime'] = latest_datetime
        dh['cash'] = self.current_holdings['cash']
        dh['commission'] = self.current_holdings['commission']
        dh['total'] = self.current_holdings['cash']

        for s in self.symbol_list:
            # Approximate the real time value
            market_value = self.bars.get_latest_bars(s)[0][1]['close']
            dh[s] = self.current_positions[s] * market_value
            dh['total'] += dh[s]
        self.all_holdings.append(dh)

    def update_positions_from_fill(self, fill_event):
        """
        Takes a FillEvent object and updates the current positions
        list. This entry in the positions list is simply a copy of
        the previous one, with the quantity modified.
        """
        fill_direction = 0
        if fill_event.direction == 'BUY':
            fill_direction = 1
        if fill_event.direction == 'SELL':
            fill_direction = -1

        self.current_positions[fill_event.symbol] += fill_direction * fill_event.quantity

    def update_holdings_from_fill(self, fill_event):
        """
        Takes a FillEvent object and updates the current holdings
        list. This entry in the holdings list is simply a copy of
        the previous one, with the cash and commission modified.
        """
        fill_direction = 0
        if fill_event.direction == 'BUY':
            fill_direction = 1
        if fill_event.direction == 'SELL':
            fill_direction = -1

        fill_cost = self.bars.get_latest_bars(fill_event.symbol)[0][1]['close'] * fill_event.quantity
        self.current_holdings['cash'] -= (fill_direction * fill_cost) + fill_event.commission
        self.current_holdings['commission'] += fill_event.commission
        

    def generate_order(self, signal_event):
        """
        Generates an OrderEvent object based on a SignalEvent.
        """
        order = None

        symbol = signal_event.symbol
        signal_type = signal_event.signal_type
        strength = signal_event.strength

        mkt_quantity = 100  # Fixed quantity for now
        cur_quantity = self.current_positions[symbol]

        if signal_type == 'LONG' and cur_quantity == 0:
            order = OrderEvent(symbol, 'MKT', mkt_quantity, 'BUY')
        if signal_type == 'SHORT' and cur_quantity == 0:
            order = OrderEvent(symbol, 'MKT', mkt_quantity, 'SELL')
        if signal_type == 'EXIT' and cur_quantity > 0:
            order = OrderEvent(symbol, 'MKT', abs(cur_quantity), 'SELL')
        if signal_type == 'EXIT' and cur_quantity < 0:
            order = OrderEvent(symbol, 'MKT', abs(cur_quantity), 'BUY')

        if order:
            self.events.put(order)

    def update_signal(self, event):
        """
        Acts on a SignalEvent to generate new orders.
        """
        if event.type == 'SIGNAL':
            self.generate_order(event)

    def update_fill(self, event):
        """
        Updates the portfolio current positions and holdings from a FillEvent.
        """
        if event.type == 'FILL':
            self.update_positions_from_fill(event)
            self.update_holdings_from_fill(event)
