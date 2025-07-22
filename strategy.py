from events import SignalEvent
import logging

logger = logging.getLogger(__name__)


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
        self.data_handler = (
            data_handler  # Store data_handler for historical data access
        )
        self.portfolio = portfolio
        self.execution_handler = execution_handler
        self.bought = False
        self.bar_count = 0

    def calculate_signals(self, event):
        """
        For this strategy, we will demonstrate various order types.
        """
        if event.type == "MARKET":
            self.bar_count += 1

            # Demonstrate accessing historical data
            historical_bars = self.data_handler.get_historical_bars(self.symbol, N=3)
            if not historical_bars.empty:
                logger.debug(
                    f"Latest 3 historical bars for {self.symbol}:\n{historical_bars}"
                )

            # Demonstrate accessing portfolio and execution handler state
            logger.debug(f"Current cash: {self.portfolio.current_holdings['cash']:.2f}")
            logger.debug(
                f"Current {self.symbol} position: {self.portfolio.current_positions[self.symbol]}"
            )
            logger.debug(f"Open orders: {len(self.execution_handler.orders)}")

            current_price = self.data_handler.get_latest_bars(self.symbol)[0][1][
                "close"
            ]

            if not self.bought and self.bar_count == 1:
                # Initial Market Buy Order
                logger.info("Placing initial Market BUY order.")
                signal = SignalEvent(
                    1,
                    self.symbol,
                    event.timeindex,
                    "LONG",
                    1.0,
                    sizing_type="FIXED_SHARES",
                    sizing_value=100,
                    order_type="MKT",
                    immediate_fill=False,
                )
                self.events.put(signal)
                self.bought = True

            elif self.bought and self.bar_count == 3:
                # Limit Buy Order (buy if price drops)
                limit_price = current_price * 0.95  # 5% below current price
                logger.info(f"Placing Limit BUY order at {limit_price:.2f}.")
                signal = SignalEvent(
                    1,
                    self.symbol,
                    event.timeindex,
                    "LONG",
                    1.0,
                    sizing_type="FIXED_SHARES",
                    sizing_value=50,
                    order_type="LMT",
                    limit_price=limit_price,
                )
                self.events.put(signal)

            elif self.bought and self.bar_count == 5:
                # Stop Sell Order (sell if price rises significantly)
                stop_price = current_price * 1.05  # 5% above current price
                logger.info(f"Placing Stop SELL order at {stop_price:.2f}.")
                signal = SignalEvent(
                    1,
                    self.symbol,
                    event.timeindex,
                    "EXIT",
                    1.0,
                    sizing_type="FIXED_SHARES",
                    sizing_value=self.portfolio.current_positions[self.symbol],
                    order_type="STP",
                    stop_price=stop_price,
                )
                self.events.put(signal)

            elif self.bought and self.bar_count == 7:
                # Trailing Stop Sell Order
                trail_price_offset = current_price * 0.02  # 2% trailing stop
                logger.info(
                    f"Placing Trailing Stop SELL order with offset {trail_price_offset:.2f}."
                )
                signal = SignalEvent(
                    1,
                    self.symbol,
                    event.timeindex,
                    "EXIT",
                    1.0,
                    sizing_type="FIXED_SHARES",
                    sizing_value=self.portfolio.current_positions[self.symbol],
                    order_type="TRAIL",
                    trail_price=trail_price_offset,
                )
                self.events.put(signal)

            elif self.bought and self.bar_count == 9:
                # Immediate Fill Market Buy Order (for demonstration of immediate_fill)
                logger.info("Placing Immediate Fill Market BUY order.")
                signal = SignalEvent(
                    1,
                    self.symbol,
                    event.timeindex,
                    "LONG",
                    1.0,
                    sizing_type="FIXED_SHARES",
                    sizing_value=20,
                    order_type="MKT",
                    immediate_fill=True,
                )
                self.events.put(signal)

            elif self.bought and self.bar_count == 10:
                # Final Exit Market Order
                logger.info("Placing final Market EXIT order.")
                signal = SignalEvent(
                    1,
                    self.symbol,
                    event.timeindex,
                    "EXIT",
                    1.0,
                    sizing_type="FIXED_SHARES",
                    sizing_value=self.portfolio.current_positions[self.symbol],
                    order_type="MKT",
                    immediate_fill=False,
                )
                self.events.put(signal)
                self.bought = (
                    False  # Reset for potential re-entry if backtest continues
                )


class StressTestStrategy(Strategy):
    """
    A strategy designed to stress-test the system by using various order types
    and features in a predictable sequence.
    """

    def __init__(self, symbol, events, data_handler, portfolio, execution_handler):
        self.symbol = symbol
        self.events = events
        self.data_handler = data_handler
        self.portfolio = portfolio
        self.execution_handler = execution_handler
        self.bar_count = 0

    def calculate_signals(self, event):
        if event.type != "MARKET":
            return

        self.bar_count += 1
        current_price = self.data_handler.get_latest_bars(self.symbol)[0][1]["close"]

        # --- STRESS TEST SEQUENCE ---

        # 1. Day 1: Initial LONG with Market Order (Fixed Shares)
        if self.bar_count == 1:
            logger.info(
                f"DAY {self.bar_count}: Initial MKT BUY (10 shares @ {current_price})"
            )
            signal = SignalEvent(
                1,
                self.symbol,
                event.timeindex,
                "LONG",
                1.0,
                sizing_type="FIXED_SHARES",
                sizing_value=10,
                order_type="MKT",
            )
            self.events.put(signal)

        # 2. Day 2: Add to LONG with Market Order (% Equity)
        elif self.bar_count == 2:
            logger.info(
                f"DAY {self.bar_count}: Add to LONG with MKT BUY (10% of equity @ {current_price})"
            )
            signal = SignalEvent(
                1,
                self.symbol,
                event.timeindex,
                "LONG",
                1.0,
                sizing_type="PERCENT_EQUITY",
                sizing_value=0.10,
                order_type="MKT",
            )
            self.events.put(signal)

        # 3. Day 3: Place a LIMIT order to buy on a dip
        elif self.bar_count == 3:
            limit_price = 95.0
            logger.info(
                f"DAY {self.bar_count}: Placing LMT BUY order (5 shares @ {limit_price})"
            )
            signal = SignalEvent(
                1,
                self.symbol,
                event.timeindex,
                "LONG",
                1.0,
                sizing_type="FIXED_SHARES",
                sizing_value=5,
                order_type="LMT",
                limit_price=limit_price,
            )
            self.events.put(signal)

        # 4. Day 4: Place a STOP order to sell on a price drop (Stop-Loss)
        elif self.bar_count == 4:
            stop_price = 96.0
            logger.info(
                f"DAY {self.bar_count}: Placing STP SELL order (all shares @ {stop_price})"
            )
            signal = SignalEvent(
                1,
                self.symbol,
                event.timeindex,
                "EXIT",
                1.0,
                sizing_type="FIXED_SHARES",
                sizing_value=self.portfolio.current_positions[self.symbol],
                order_type="STP",
                stop_price=stop_price,
            )
            self.events.put(signal)

        # 5. Day 5: Flip position to SHORT
        elif self.bar_count == 5:
            logger.info(
                f"DAY {self.bar_count}: Flipping to SHORT with MKT SELL (30 shares @ {current_price})"
            )
            signal = SignalEvent(
                1,
                self.symbol,
                event.timeindex,
                "SHORT",
                1.0,
                sizing_type="FIXED_SHARES",
                sizing_value=30,
                order_type="MKT",
            )
            self.events.put(signal)

        # 6. Day 6: Place a TRAIL BUY order to protect short position
        elif self.bar_count == 6:
            trail_offset = 2.0  # Trail by $2
            logger.info(
                f"DAY {self.bar_count}: Placing TRAIL BUY order (all shares with ${trail_offset} trail)"
            )
            signal = SignalEvent(
                1,
                self.symbol,
                event.timeindex,
                "EXIT",
                1.0,
                sizing_type="FIXED_SHARES",
                sizing_value=abs(self.portfolio.current_positions[self.symbol]),
                order_type="TRAIL",
                trail_price=trail_offset,
            )
            self.events.put(signal)

        # 7. Day 8: Use an IMMEDIATE FILL order
        elif self.bar_count == 8:
            logger.info(
                f"DAY {self.bar_count}: Placing Immediate Fill MKT BUY (5 shares @ {current_price})"
            )
            signal = SignalEvent(
                1,
                self.symbol,
                event.timeindex,
                "LONG",
                1.0,
                sizing_type="FIXED_SHARES",
                sizing_value=5,
                order_type="MKT",
                immediate_fill=True,
            )
            self.events.put(signal)

        # 8. Day 10: Final EXIT of all positions
        elif self.bar_count == 10:
            if self.portfolio.current_positions[self.symbol] != 0:
                logger.info(f"DAY {self.bar_count}: Final MKT EXIT of all positions.")
                signal = SignalEvent(
                    1,
                    self.symbol,
                    event.timeindex,
                    "EXIT",
                    1.0,
                    sizing_type="FIXED_SHARES",
                    sizing_value=abs(self.portfolio.current_positions[self.symbol]),
                    order_type="MKT",
                )
                self.events.put(signal)
