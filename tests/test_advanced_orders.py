import pytest
import os
import sys
import pandas as pd

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from event_bus import EventBus
from events import MarketEvent, OrderEvent, FillEvent, CancelOrderEvent
from data_handler import CSVDataHandler
from execution_handler import SimulatedExecutionHandler

@pytest.fixture
def setup_csv_data(tmp_path):
    # Create a temporary directory for CSV files
    csv_dir = tmp_path / "data"
    csv_dir.mkdir()

    # Create a dummy CSV file with more varied data for testing
    aapl_csv_content = """
datetime,open,high,low,close,volume
2023-01-01,100.00,101.00,99.00,100.50,100000
2023-01-02,100.50,102.00,100.00,101.50,120000
2023-01-03,101.50,103.00,101.00,102.50,150000
2023-01-04,102.50,104.00,102.00,103.50,180000
2023-01-05,103.50,105.00,103.00,104.50,200000
2023-01-06,104.50,106.00,104.00,105.50,220000
2023-01-07,105.50,107.00,105.00,106.50,240000
2023-01-08,106.50,108.00,106.00,107.50,260000
2023-01-09,107.50,109.00,107.00,108.50,280000
2023-01-10,108.50,110.00,108.00,109.50,300000
"""
    (csv_dir / "AAPL.csv").write_text(aapl_csv_content)

    return csv_dir

# --- Limit Order Tests ---

def test_limit_buy_fill_at_limit_price(setup_csv_data):
    csv_dir = setup_csv_data
    event_bus = EventBus()
    data_handler = CSVDataHandler(event_bus, str(csv_dir), ["AAPL"])
    execution_handler = SimulatedExecutionHandler(event_bus, data_handler)

    order = OrderEvent("AAPL", "LMT", 100, "BUY", limit_price=100.00)
    execution_handler.execute_order(order)

    data_handler.update_bars() # 2023-01-01: Open=100.00, Low=99.00
    market_event = event_bus.get()
    execution_handler.update(market_event)

    assert not event_bus.empty()
    fill_event = event_bus.get()
    assert fill_event.type == 'FILL'
    assert fill_event.symbol == 'AAPL'
    assert fill_event.quantity == 100
    assert fill_event.direction == 'BUY'
    assert fill_event.fill_cost == pytest.approx(100.00 * 100) # Filled at limit price

def test_limit_buy_fill_at_better_price(setup_csv_data):
    csv_dir = setup_csv_data
    event_bus = EventBus()
    data_handler = CSVDataHandler(event_bus, str(csv_dir), ["AAPL"])
    execution_handler = SimulatedExecutionHandler(event_bus, data_handler)

    order = OrderEvent("AAPL", "LMT", 100, "BUY", limit_price=100.50)
    execution_handler.execute_order(order)

    data_handler.update_bars() # 2023-01-01: Open=100.00, Low=99.00
    market_event = event_bus.get()
    execution_handler.update(market_event)

    assert not event_bus.empty()
    fill_event = event_bus.get()
    assert fill_event.type == 'FILL'
    assert fill_event.fill_cost == pytest.approx(100.00 * 100) # Filled at open price (better than limit)

def test_limit_buy_no_fill(setup_csv_data):
    csv_dir = setup_csv_data
    event_bus = EventBus()
    data_handler = CSVDataHandler(event_bus, str(csv_dir), ["AAPL"])
    execution_handler = SimulatedExecutionHandler(event_bus, data_handler)

    order = OrderEvent("AAPL", "LMT", 100, "BUY", limit_price=98.00) # Below any price in 2023-01-01
    execution_handler.execute_order(order)

    data_handler.update_bars() # 2023-01-01
    market_event = event_bus.get()
    execution_handler.update(market_event)

    assert event_bus.empty() # Should not be filled

def test_limit_sell_fill_at_limit_price(setup_csv_data):
    csv_dir = setup_csv_data
    event_bus = EventBus()
    data_handler = CSVDataHandler(event_bus, str(csv_dir), ["AAPL"])
    execution_handler = SimulatedExecutionHandler(event_bus, data_handler)

    order = OrderEvent("AAPL", "LMT", 100, "SELL", limit_price=101.00)
    execution_handler.execute_order(order)

    data_handler.update_bars() # 2023-01-01: Open=100.00, High=101.00
    market_event = event_bus.get()
    execution_handler.update(market_event)

    assert not event_bus.empty()
    fill_event = event_bus.get()
    assert fill_event.type == 'FILL'
    assert fill_event.symbol == 'AAPL'
    assert fill_event.quantity == 100
    assert fill_event.direction == 'SELL'
    assert fill_event.fill_cost == pytest.approx(101.00 * 100) # Filled at limit price

def test_limit_sell_fill_at_better_price(setup_csv_data):
    csv_dir = setup_csv_data
    event_bus = EventBus()
    data_handler = CSVDataHandler(event_bus, str(csv_dir), ["AAPL"])
    execution_handler = SimulatedExecutionHandler(event_bus, data_handler)

    order = OrderEvent("AAPL", "LMT", 100, "SELL", limit_price=100.00)
    execution_handler.execute_order(order)

    data_handler.update_bars() # 2023-01-01: Open=100.00, High=101.00
    market_event = event_bus.get()
    execution_handler.update(market_event)

    assert not event_bus.empty()
    fill_event = event_bus.get()
    assert fill_event.type == 'FILL'
    assert fill_event.fill_cost == pytest.approx(100.00 * 100) # Filled at open price (better than limit)

def test_limit_sell_no_fill(setup_csv_data):
    csv_dir = setup_csv_data
    event_bus = EventBus()
    data_handler = CSVDataHandler(event_bus, str(csv_dir), ["AAPL"])
    execution_handler = SimulatedExecutionHandler(event_bus, data_handler)

    order = OrderEvent("AAPL", "LMT", 100, "SELL", limit_price=102.00) # Above any price in 2023-01-01
    execution_handler.execute_order(order)

    data_handler.update_bars() # 2023-01-01
    market_event = event_bus.get()
    execution_handler.update(market_event)

    assert event_bus.empty() # Should not be filled

# --- Stop Order Tests ---

def test_stop_buy_fill(setup_csv_data):
    csv_dir = setup_csv_data
    event_bus = EventBus()
    data_handler = CSVDataHandler(event_bus, str(csv_dir), ["AAPL"])
    execution_handler = SimulatedExecutionHandler(event_bus, data_handler)

    order = OrderEvent("AAPL", "STP", 100, "BUY", stop_price=101.50)
    execution_handler.execute_order(order)

    data_handler.update_bars() # 2023-01-01: High=101.00
    market_event = event_bus.get()
    execution_handler.update(market_event)
    assert event_bus.empty() # Not triggered yet

    data_handler.update_bars() # 2023-01-02: High=102.00 (triggered)
    market_event = event_bus.get()
    execution_handler.update(market_event)

    assert not event_bus.empty()
    fill_event = event_bus.get()
    assert fill_event.type == 'FILL'
    assert fill_event.fill_cost == pytest.approx(102.00 * 100) # Filled at open or higher

def test_stop_sell_fill(setup_csv_data):
    csv_dir = setup_csv_data
    event_bus = EventBus()
    data_handler = CSVDataHandler(event_bus, str(csv_dir), ["AAPL"])
    execution_handler = SimulatedExecutionHandler(event_bus, data_handler)

    order = OrderEvent("AAPL", "STP", 100, "SELL", stop_price=100.00)
    execution_handler.execute_order(order)

    data_handler.update_bars() # 2023-01-01: Low=99.00 (triggered)
    market_event = event_bus.get()
    execution_handler.update(market_event)

    assert not event_bus.empty()
    fill_event = event_bus.get()
    assert fill_event.type == 'FILL'
    assert fill_event.fill_cost == pytest.approx(100.00 * 100) # Filled at open or lower

# --- Stop-Limit Order Tests ---

def test_stop_limit_buy_trigger_and_fill(setup_csv_data):
    csv_dir = setup_csv_data
    event_bus = EventBus()
    data_handler = CSVDataHandler(event_bus, str(csv_dir), ["AAPL"])
    execution_handler = SimulatedExecutionHandler(event_bus, data_handler)

    order = OrderEvent("AAPL", "STP_LMT", 100, "BUY", stop_price=101.50, limit_price=102.00)
    execution_handler.execute_order(order)

    data_handler.update_bars() # 2023-01-01: High=101.00
    market_event = event_bus.get()
    execution_handler.update(market_event)
    assert event_bus.empty() # Not triggered yet

    data_handler.update_bars() # 2023-01-02: High=102.00 (triggered), Open=100.50, Low=100.00
    market_event = event_bus.get()
    execution_handler.update(market_event)

    # Should be converted to a limit order and filled at 100.50 (open) as it's better than limit
    assert not event_bus.empty()
    fill_event = event_bus.get()
    assert fill_event.type == 'FILL'
    assert fill_event.fill_cost == pytest.approx(100.50 * 100)

def test_stop_limit_sell_trigger_and_fill(setup_csv_data):
    csv_dir = setup_csv_data
    event_bus = EventBus()
    data_handler = CSVDataHandler(event_bus, str(csv_dir), ["AAPL"])
    execution_handler = SimulatedExecutionHandler(event_bus, data_handler)

    order = OrderEvent("AAPL", "STP_LMT", 100, "SELL", stop_price=100.50, limit_price=100.00)
    execution_handler.execute_order(order)

    data_handler.update_bars() # 2023-01-01: Low=99.00 (triggered), Open=100.00, High=101.00
    market_event = event_bus.get()
    execution_handler.update(market_event)

    # Should be converted to a limit order and filled at 100.00 (limit) as it's better than open
    assert not event_bus.empty()
    fill_event = event_bus.get()
    assert fill_event.type == 'FILL'
    assert fill_event.fill_cost == pytest.approx(100.00 * 100)

# --- Trailing Stop Order Tests ---

def test_trailing_stop_buy_fill(setup_csv_data):
    csv_dir = setup_csv_data
    event_bus = EventBus()
    data_handler = CSVDataHandler(event_bus, str(csv_dir), ["AAPL"])
    execution_handler = SimulatedExecutionHandler(event_bus, data_handler)

    # Trailing stop 1.00 below highest close
    order = OrderEvent("AAPL", "TRAIL", 100, "BUY", trail_price=1.00)
    execution_handler.execute_order(order)

    # 2023-01-01: Close=100.50, Trail=99.50. Low=99.00. Should trigger.
    data_handler.update_bars()
    market_event = event_bus.get()
    execution_handler.update(market_event)

    assert not event_bus.empty()
    fill_event = event_bus.get()
    assert fill_event.type == 'FILL'
    assert fill_event.symbol == 'AAPL'
    assert fill_event.quantity == 100
    assert fill_event.direction == 'BUY'
    assert fill_event.fill_cost == pytest.approx(100.00 * 100) # Filled at open price

# --- Partial Fill Tests ---

def test_partial_fill_market_order(setup_csv_data):
    csv_dir = setup_csv_data
    event_bus = EventBus()
    data_handler = CSVDataHandler(event_bus, str(csv_dir), ["AAPL"])
    execution_handler = SimulatedExecutionHandler(event_bus, data_handler, partial_fill_volume_pct=0.1) # 10% of bar volume

    # Simulate a market order for 50000 shares
    order = OrderEvent("AAPL", "MKT", 50000, "BUY")
    execution_handler.execute_order(order)

    # First market update: should partially fill (10% of 100000 volume = 10000 shares)
    data_handler.update_bars() # 2023-01-01: Volume=100000
    market_event = event_bus.get()
    execution_handler.update(market_event)

    assert not event_bus.empty()
    fill_event1 = event_bus.get()
    assert fill_event1.type == 'FILL'
    assert fill_event1.quantity == 10000
    assert fill_event1.partial_fill is True
    assert execution_handler.orders[1].filled_quantity == 10000

    # Second market update: should partially fill again (10% of 120000 volume = 12000 shares)
    data_handler.update_bars() # 2023-01-02: Volume=120000
    market_event = event_bus.get()
    execution_handler.update(market_event)

    assert not event_bus.empty()
    fill_event2 = event_bus.get()
    assert fill_event2.type == 'FILL'
    assert fill_event2.quantity == 12000
    assert fill_event2.partial_fill is True
    assert execution_handler.orders[1].filled_quantity == 22000

    # Third market update: should partially fill again (10% of 150000 volume = 15000 shares)
    data_handler.update_bars() # 2023-01-03: Volume=150000
    market_event = event_bus.get()
    execution_handler.update(market_event)

    assert not event_bus.empty()
    fill_event3 = event_bus.get()
    assert fill_event3.type == 'FILL'
    assert fill_event3.quantity == 15000
    assert fill_event3.partial_fill is True
    assert execution_handler.orders[1].filled_quantity == 37000

    # Fourth market update: should fill the remaining (50000 - 37000 = 13000 shares)
    data_handler.update_bars() # 2023-01-04: Volume=180000
    market_event = event_bus.get()
    execution_handler.update(market_event)

    assert not event_bus.empty()
    fill_event4 = event_bus.get()
    assert fill_event4.type == 'FILL'
    assert fill_event4.quantity == 13000
    assert fill_event4.partial_fill is False
    assert execution_handler.orders.get(1) is None # Order should be removed

# --- Slippage Tests ---

def test_slippage_buy_order(setup_csv_data):
    csv_dir = setup_csv_data
    event_bus = EventBus()
    data_handler = CSVDataHandler(event_bus, str(csv_dir), ["AAPL"])
    execution_handler = SimulatedExecutionHandler(event_bus, data_handler, slippage_bps=10) # 10 basis points slippage

    order = OrderEvent("AAPL", "MKT", 100, "BUY")
    execution_handler.execute_order(order)

    data_handler.update_bars() # 2023-01-01: Open=100.00
    market_event = event_bus.get()
    execution_handler.update(market_event)

    assert not event_bus.empty()
    fill_event = event_bus.get()
    assert fill_event.type == 'FILL'
    expected_fill_price = 100.00 * (1 + 10 / 10000.0) # 100.00 * 1.001 = 100.1
    assert fill_event.fill_cost == pytest.approx(expected_fill_price * 100)

def test_slippage_sell_order(setup_csv_data):
    csv_dir = setup_csv_data
    event_bus = EventBus()
    data_handler = CSVDataHandler(event_bus, str(csv_dir), ["AAPL"])
    execution_handler = SimulatedExecutionHandler(event_bus, data_handler, slippage_bps=10) # 10 basis points slippage

    order = OrderEvent("AAPL", "MKT", 100, "SELL")
    execution_handler.execute_order(order)

    data_handler.update_bars() # 2023-01-01: Open=100.00
    market_event = event_bus.get()
    execution_handler.update(market_event)

    assert not event_bus.empty()
    fill_event = event_bus.get()
    assert fill_event.type == 'FILL'
    expected_fill_price = 100.00 * (1 - 10 / 10000.0) # 100.00 * 0.999 = 99.9
    assert fill_event.fill_cost == pytest.approx(expected_fill_price * 100)

# --- Order Cancellation Tests ---

def test_cancel_pending_order(setup_csv_data):
    csv_dir = setup_csv_data
    event_bus = EventBus()
    data_handler = CSVDataHandler(event_bus, str(csv_dir), ["AAPL"])
    execution_handler = SimulatedExecutionHandler(event_bus, data_handler)

    # Create a limit order that won't be filled immediately
    order = OrderEvent("AAPL", "LMT", 100, "BUY", limit_price=90.00)
    execution_handler.execute_order(order)

    # Ensure the order is in the active orders list
    assert 1 in execution_handler.orders

    # Send a cancel order event
    cancel_event = CancelOrderEvent(1)
    execution_handler.execute_order(cancel_event)

    # Check if the order is removed from active orders
    assert 1 not in execution_handler.orders

    # Simulate market update - no fill event should be generated for the canceled order
    data_handler.update_bars() # 2023-01-01
    market_event = event_bus.get()
    execution_handler.update(market_event)

    assert event_bus.empty() # No fill event should be generated