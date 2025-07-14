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
        self.open_positions_details = {}  # To track entry details for open positions
        self.closed_trades = []  # To store details of closed trades

    def _calculate_quantity(self, symbol, sizing_type, sizing_value, direction):
        """
        Calculates the quantity of shares based on the sizing type and value.
        """
        current_price = self.bars.get_latest_bars(symbol)[0][1]['close']
        if current_price == 0:
            return 0 # Avoid division by zero

        if sizing_type == 'FIXED_SHARES':
            return int(sizing_value)
        elif sizing_type == 'PERCENT_EQUITY':
            total_equity = self.current_holdings['total']
            capital_to_invest = total_equity * sizing_value
            quantity = int(capital_to_invest / current_price)
            return quantity
        elif sizing_type == 'FIXED_CAPITAL':
            quantity = int(sizing_value / current_price)
            return quantity
        else:
            # Default to a fixed quantity if sizing type is not specified or recognized
            return 100 # Default quantity

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

        fill_cost = fill_event.fill_cost
        self.current_holdings['cash'] -= (fill_direction * fill_cost) + fill_event.commission
        self.current_holdings['commission'] += fill_event.commission
        

    def _track_trades_from_fill(self, fill_event):
        """
        Tracks individual trades (entry, exit, PnL, duration) based on fill events.
        Handles opening, adding to, and closing both long and short positions.
        """
        symbol = fill_event.symbol
        fill_quantity = fill_event.quantity
        fill_price = fill_event.fill_cost / fill_quantity if fill_quantity != 0 else 0.0
        fill_time = fill_event.timeindex
        fill_direction = fill_event.direction # 'BUY' or 'SELL'

        # Helper to create a closed trade entry
        def _create_closed_trade(entry_time, exit_time, entry_price, exit_price, quantity, direction, entry_commission, exit_commission):
            pnl = 0.0
            if direction == 'LONG':
                pnl = (exit_price - entry_price) * quantity - (entry_commission + exit_commission)
            elif direction == 'SHORT':
                pnl = (entry_price - exit_price) * quantity - (entry_commission + exit_commission)
            
            trade = {
                'symbol': symbol,
                'entry_time': entry_time,
                'exit_time': exit_time,
                'entry_price': entry_price,
                'exit_price': exit_price,
                'quantity': quantity,
                'direction': direction,
                'pnl': pnl,
                'commission': entry_commission + exit_commission,
                'duration': (exit_time - entry_time).total_seconds() / (60*60*24) # Duration in days
            }
            self.closed_trades.append(trade)

        # Get current open position details for the symbol
        existing_pos = self.open_positions_details.get(symbol)

        if fill_direction == 'BUY':
            if existing_pos and existing_pos['direction'] == 'SHORT':
                # Closing (partially or fully) a short position
                close_quantity = min(fill_quantity, existing_pos['quantity'])
                
                # Calculate proportional entry commission for the closed portion
                entry_commission_for_closed_portion = (existing_pos['total_entry_commission'] / existing_pos['quantity']) * close_quantity

                _create_closed_trade(
                    existing_pos['entry_time'], fill_time,
                    existing_pos['entry_price'], fill_price,
                    close_quantity, 'SHORT',
                    entry_commission_for_closed_portion, fill_event.commission
                )
                
                existing_pos['quantity'] -= close_quantity
                existing_pos['total_entry_commission'] -= entry_commission_for_closed_portion

                if existing_pos['quantity'] <= 0:
                    del self.open_positions_details[symbol]
                
                remaining_fill_quantity = fill_quantity - close_quantity
                if remaining_fill_quantity > 0:
                    # If remaining fill, it's opening a new long position
                    self.open_positions_details[symbol] = {
                        'entry_time': fill_time,
                        'entry_price': fill_price,
                        'quantity': remaining_fill_quantity,
                        'direction': 'LONG',
                        'total_entry_commission': fill_event.commission - (fill_event.commission / fill_quantity) * close_quantity # Adjust commission for the new position
                    }
            else:
                # Opening or adding to a long position
                if not existing_pos:
                    self.open_positions_details[symbol] = {
                        'entry_time': fill_time,
                        'entry_price': fill_price,
                        'quantity': fill_quantity,
                        'direction': 'LONG',
                        'total_entry_commission': fill_event.commission
                    }
                else: # existing_pos and existing_pos['direction'] == 'LONG'
                    total_quantity = existing_pos['quantity'] + fill_quantity
                    existing_pos['entry_price'] = (existing_pos['entry_price'] * existing_pos['quantity'] + fill_price * fill_quantity) / total_quantity
                    existing_pos['quantity'] = total_quantity
                    existing_pos['total_entry_commission'] += fill_event.commission

        elif fill_direction == 'SELL':
            if existing_pos and existing_pos['direction'] == 'LONG':
                # Closing (partially or fully) a long position
                close_quantity = min(fill_quantity, existing_pos['quantity'])

                # Calculate proportional entry commission for the closed portion
                entry_commission_for_closed_portion = (existing_pos['total_entry_commission'] / existing_pos['quantity']) * close_quantity

                _create_closed_trade(
                    existing_pos['entry_time'], fill_time,
                    existing_pos['entry_price'], fill_price,
                    close_quantity, 'LONG',
                    entry_commission_for_closed_portion, fill_event.commission
                )

                existing_pos['quantity'] -= close_quantity
                existing_pos['total_entry_commission'] -= entry_commission_for_closed_portion

                if existing_pos['quantity'] <= 0:
                    del self.open_positions_details[symbol]
                
                remaining_fill_quantity = fill_quantity - close_quantity
                if remaining_fill_quantity > 0:
                    # If remaining fill, it's opening a new short position
                    self.open_positions_details[symbol] = {
                        'entry_time': fill_time,
                        'entry_price': fill_price,
                        'quantity': remaining_fill_quantity,
                        'direction': 'SHORT',
                        'total_entry_commission': fill_event.commission - (fill_event.commission / fill_quantity) * close_quantity # Adjust commission for the new position
                    }
            else:
                # Opening or adding to a short position
                if not existing_pos:
                    self.open_positions_details[symbol] = {
                        'entry_time': fill_time,
                        'entry_price': fill_price,
                        'quantity': fill_quantity,
                        'direction': 'SHORT',
                        'total_entry_commission': fill_event.commission
                    }
                else: # existing_pos and existing_pos['direction'] == 'SHORT'
                    total_quantity = existing_pos['quantity'] + fill_quantity
                    existing_pos['entry_price'] = (existing_pos['entry_price'] * existing_pos['quantity'] + fill_price * fill_quantity) / total_quantity
                    existing_pos['quantity'] = total_quantity
                    existing_pos['total_entry_commission'] += fill_event.commission
        

    def generate_order(self, signal_event):
        """
        Generates an OrderEvent object based on a SignalEvent.
        """
        order = None

        symbol = signal_event.symbol
        signal_type = signal_event.signal_type
        strength = signal_event.strength
        sizing_type = signal_event.sizing_type
        sizing_value = signal_event.sizing_value

        # Calculate quantity based on sizing options
        mkt_quantity = self._calculate_quantity(symbol, sizing_type, sizing_value, signal_type)

        if mkt_quantity <= 0:
            print(f"Warning: Calculated quantity for {symbol} is zero or negative. No order generated.")
            return

        cur_quantity = self.current_positions[symbol]

        if signal_type == 'LONG' and cur_quantity == 0:
            order = OrderEvent(symbol, 'MKT', mkt_quantity, 'BUY', immediate_fill=False)
        elif signal_type == 'SHORT' and cur_quantity == 0:
            order = OrderEvent(symbol, 'MKT', mkt_quantity, 'SELL', immediate_fill=False)
        elif signal_type == 'EXIT' and cur_quantity > 0:
            order = OrderEvent(symbol, 'MKT', abs(cur_quantity), 'SELL', immediate_fill=False)
        elif signal_type == 'EXIT' and cur_quantity < 0:
            order = OrderEvent(symbol, 'MKT', abs(cur_quantity), 'BUY', immediate_fill=False)
        elif signal_type == 'MKT_IMMEDIATE_LONG' and cur_quantity == 0:
            order = OrderEvent(symbol, 'MKT', mkt_quantity, 'BUY', immediate_fill=True)
        elif signal_type == 'MKT_IMMEDIATE_SHORT' and cur_quantity == 0:
            order = OrderEvent(symbol, 'MKT', mkt_quantity, 'SELL', immediate_fill=True)
        elif signal_type == 'MKT_IMMEDIATE_EXIT_LONG' and cur_quantity > 0:
            order = OrderEvent(symbol, 'MKT', abs(cur_quantity), 'SELL', immediate_fill=True)
        elif signal_type == 'MKT_IMMEDIATE_EXIT_SHORT' and cur_quantity < 0:
            order = OrderEvent(symbol, 'MKT', abs(cur_quantity), 'BUY', immediate_fill=True)

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
        Also tracks individual trades.
        """
        if event.type == 'FILL':
            self.update_positions_from_fill(event)
            self.update_holdings_from_fill(event)
            self._track_trades_from_fill(event)
