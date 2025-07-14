import pytest
import os
import sys
import pandas as pd

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from event_bus import EventBus
from events import MarketEvent, SignalEvent, OrderEvent, FillEvent
from data_handler import CSVDataHandler
from strategy import BuyAndHoldStrategy
from portfolio import Portfolio
from execution_handler import SimulatedExecutionHandler

class MockBars:
    def get_latest_bars(self, symbol):
        return [(pd.Timestamp('2023-01-01'), {'open': 100, 'high': 101, 'low': 99, 'close': 100.5, 'volume': 100000})]

# Test for EventBus
def test_event_bus_put_get():
    event_bus = EventBus()
    event = MarketEvent(pd.Timestamp('2023-01-01'))
    event_bus.put(event)
    assert not event_bus.empty()
    retrieved_event = event_bus.get()
    assert retrieved_event.type == 'MARKET'
    assert event_bus.empty()

def test_event_bus_empty():
    event_bus = EventBus()
    assert event_bus.empty()
    event_bus.put(MarketEvent(pd.Timestamp('2023-01-01')))

    assert not event_bus.empty()
    event_bus.get()
    assert event_bus.empty()

# Test for CSVDataHandler
@pytest.fixture
def setup_csv_data(tmp_path):
    # Create a temporary directory for CSV files
    csv_dir = tmp_path / "data"
    csv_dir.mkdir()

    # Create a dummy CSV file
    aapl_csv_content = """
datetime,open,high,low,close,volume
2023-01-01,100,101,99,100.5,100000
2023-01-02,100.5,102,100,101.5,120000
2023-01-03,101.5,103,101,102.5,150000
"""
    (csv_dir / "AAPL.csv").write_text(aapl_csv_content)

    # Create another dummy CSV file for multiple symbols
    goog_csv_content = """
datetime,open,high,low,close,volume
2023-01-01,200,201,199,200.5,200000
2023-01-02,200.5,202,200,201.5,240000
2023-01-03,201.5,203,201,202.5,300000
"""
    (csv_dir / "GOOG.csv").write_text(goog_csv_content)

    return csv_dir

def test_csv_data_handler_initialization(setup_csv_data):
    csv_dir = setup_csv_data
    event_bus = EventBus()
    symbol_list = ["AAPL"]
    handler = CSVDataHandler(event_bus, str(csv_dir), symbol_list)

    assert handler.continue_backtest is True
    assert "AAPL" in handler.symbol_data
    assert isinstance(handler.symbol_data["AAPL"], pd.DataFrame)
    assert hasattr(handler.bar_generators["AAPL"], '__next__') # Check if it's an iterator

def test_csv_data_handler_update_bars(setup_csv_data):
    csv_dir = setup_csv_data
    event_bus = EventBus()
    symbol_list = ["AAPL"]
    handler = CSVDataHandler(event_bus, str(csv_dir), symbol_list)

    # First update
    handler.update_bars()
    assert not event_bus.empty()
    event = event_bus.get()
    assert event.type == 'MARKET'
    assert len(handler.latest_symbol_data["AAPL"]) == 1
    assert handler.latest_symbol_data["AAPL"][0][0] == pd.Timestamp('2023-01-01')

    # Second update
    handler.update_bars()
    assert not event_bus.empty()
    event_bus.get()
    assert len(handler.latest_symbol_data["AAPL"]) == 2
    assert handler.latest_symbol_data["AAPL"][1][0] == pd.Timestamp('2023-01-02')

    # Third update
    handler.update_bars()
    assert not event_bus.empty()
    event_bus.get()
    assert len(handler.latest_symbol_data["AAPL"]) == 3
    assert handler.latest_symbol_data["AAPL"][2][0] == pd.Timestamp('2023-01-03')

    # No more data
    handler.update_bars()
    assert event_bus.empty() # No new market event should be put
    assert handler.continue_backtest is False

def test_csv_data_handler_get_latest_bars(setup_csv_data):
    csv_dir = setup_csv_data
    event_bus = EventBus()
    symbol_list = ["AAPL"]
    handler = CSVDataHandler(event_bus, str(csv_dir), symbol_list)

    handler.update_bars() # 2023-01-01
    handler.update_bars() # 2023-01-02
    handler.update_bars() # 2023-01-03

    latest_bar = handler.get_latest_bars("AAPL")
    assert len(latest_bar) == 1
    assert latest_bar[0][0] == pd.Timestamp('2023-01-03')

    latest_two_bars = handler.get_latest_bars("AAPL", N=2)
    assert len(latest_two_bars) == 2
    assert latest_two_bars[0][0] == pd.Timestamp('2023-01-02')
    assert latest_two_bars[1][0] == pd.Timestamp('2023-01-03')

def test_csv_data_handler_multiple_symbols(setup_csv_data):
    csv_dir = setup_csv_data
    event_bus = EventBus()
    symbol_list = ["AAPL", "GOOG"]
    handler = CSVDataHandler(event_bus, str(csv_dir), symbol_list)

    handler.update_bars()
    assert len(handler.latest_symbol_data["AAPL"]) == 1
    assert len(handler.latest_symbol_data["GOOG"]) == 1
    assert handler.latest_symbol_data["AAPL"][0][0] == pd.Timestamp('2023-01-01')
    assert handler.latest_symbol_data["GOOG"][0][0] == pd.Timestamp('2023-01-01')

    handler.update_bars()
    assert len(handler.latest_symbol_data["AAPL"]) == 2
    assert len(handler.latest_symbol_data["GOOG"]) == 2
    assert handler.latest_symbol_data["AAPL"][1][0] == pd.Timestamp('2023-01-02')
    assert handler.latest_symbol_data["GOOG"][1][0] == pd.Timestamp('2023-01-02')

# Test for BuyAndHoldStrategy
def test_buy_and_hold_strategy(setup_csv_data):
    csv_dir = setup_csv_data
    event_bus = EventBus()
    symbol_list = ["AAPL"]
    data_handler = CSVDataHandler(event_bus, str(csv_dir), symbol_list)
    start_date = pd.Timestamp('2023-01-01')
    portfolio = Portfolio(data_handler, event_bus, start_date, initial_capital=100000.0)
    execution_handler = SimulatedExecutionHandler(event_bus, data_handler)
    strategy = BuyAndHoldStrategy("AAPL", event_bus, data_handler, portfolio, execution_handler)

    # Simulate a market event
    data_handler.update_bars()
    market_event = event_bus.get()
    strategy.calculate_signals(market_event)

    # Check if a SignalEvent was generated
    assert not event_bus.empty()
    signal_event = event_bus.get()
    assert signal_event.type == 'SIGNAL'
    assert signal_event.symbol == 'AAPL'
    assert signal_event.signal_type == 'LONG'

    # Ensure no more signals are generated after the first buy
    data_handler.update_bars()
    market_event = event_bus.get()
    strategy.calculate_signals(market_event)
    assert event_bus.empty()

def test_strategy_access_to_portfolio_and_execution_handler(setup_csv_data):
    csv_dir = setup_csv_data
    event_bus = EventBus()
    symbol_list = ["AAPL"]
    data_handler = CSVDataHandler(event_bus, str(csv_dir), symbol_list)
    start_date = pd.Timestamp('2023-01-01')
    portfolio = Portfolio(data_handler, event_bus, start_date, initial_capital=100000.0)
    execution_handler = SimulatedExecutionHandler(event_bus, data_handler)
    strategy = BuyAndHoldStrategy("AAPL", event_bus, data_handler, portfolio, execution_handler)

    # Simulate a market event
    data_handler.update_bars()
    market_event = event_bus.get()
    strategy.calculate_signals(market_event)

    # Assert that the strategy can access portfolio and execution handler states
    assert strategy.portfolio.current_holdings['cash'] == pytest.approx(100000.0)
    assert strategy.portfolio.current_positions['AAPL'] == 0
    assert len(strategy.execution_handler.orders) == 0 # No orders yet, as signal is processed after strategy

# Test for SimulatedExecutionHandler
def test_simulated_execution_handler():
    event_bus = EventBus()
    bars = MockBars()
    execution_handler = SimulatedExecutionHandler(event_bus, bars)

    order_event = OrderEvent("AAPL", 'MKT', 100, 'BUY')
    execution_handler.execute_order(order_event)
    market_event = MarketEvent(pd.Timestamp('2023-01-01'))
    execution_handler.update(market_event)

    assert not event_bus.empty()
    fill_event = event_bus.get()
    assert fill_event.type == 'FILL'
    assert fill_event.symbol == 'AAPL'
    assert fill_event.quantity == 100
    assert fill_event.direction == 'BUY'
    assert fill_event.exchange == 'ARCA'

# Test for Portfolio
def test_portfolio_initialization(setup_csv_data):
    csv_dir = setup_csv_data
    event_bus = EventBus()
    symbol_list = ["AAPL"]
    data_handler = CSVDataHandler(event_bus, str(csv_dir), symbol_list)
    start_date = pd.Timestamp('2023-01-01')
    portfolio = Portfolio(data_handler, event_bus, start_date, initial_capital=100000.0)

    assert portfolio.initial_capital == 100000.0
    assert portfolio.current_holdings['cash'] == 100000.0
    assert portfolio.current_holdings['total'] == 100000.0
    assert portfolio.current_positions['AAPL'] == 0

def test_portfolio_update_timeindex(setup_csv_data):
    csv_dir = setup_csv_data
    event_bus = EventBus()
    symbol_list = ["AAPL"]
    data_handler = CSVDataHandler(event_bus, str(csv_dir), symbol_list)
    start_date = pd.Timestamp('2023-01-01')
    portfolio = Portfolio(data_handler, event_bus, start_date, initial_capital=100000.0)

    data_handler.update_bars() # This will put a MarketEvent on the queue
    market_event = event_bus.get()
    portfolio.update_timeindex(market_event)

    assert len(portfolio.all_positions) == 2 # Initial + 1 update
    assert len(portfolio.all_holdings) == 2 # Initial + 1 update
    assert portfolio.all_positions[1]['datetime'] == pd.Timestamp('2023-01-01')
    assert portfolio.all_holdings[1]['datetime'] == pd.Timestamp('2023-01-01')

def test_portfolio_update_fill_and_generate_order(setup_csv_data):
    csv_dir = setup_csv_data
    event_bus = EventBus()
    symbol_list = ["AAPL"]
    data_handler = CSVDataHandler(event_bus, str(csv_dir), symbol_list)
    start_date = pd.Timestamp('2023-01-01')
    portfolio = Portfolio(data_handler, event_bus, start_date, initial_capital=100000.0)

    # Simulate a market event and update timeindex
    data_handler.update_bars()
    market_event = event_bus.get()
    portfolio.update_timeindex(market_event)

    # Simulate a signal event to generate an order
    signal_event = SignalEvent(1, "AAPL", pd.Timestamp('2023-01-01'), 'LONG', 1.0)
    portfolio.update_signal(signal_event)

    assert not event_bus.empty()
    order_event = event_bus.get()
    assert order_event.type == 'ORDER'
    assert order_event.symbol == 'AAPL'
    assert order_event.quantity == 100
    assert order_event.direction == 'BUY'

    # Simulate a fill event
    fill_event = FillEvent(
        timeindex=pd.Timestamp('2023-01-01'),
        symbol="AAPL",
        exchange='ARCA',
        quantity=100,
        direction='BUY',
        fill_cost=10050,
        commission=0.35
    )
    portfolio.update_fill(fill_event)

    assert portfolio.current_positions['AAPL'] == 100
    # 100000 (initial) - 10050 - 0.35 = 89949.65
    assert portfolio.current_holdings['cash'] == pytest.approx(89949.65)
    assert portfolio.current_holdings['commission'] == pytest.approx(0.35)
    
def test_portfolio_equity_curve(setup_csv_data):
    csv_dir = setup_csv_data
    event_bus = EventBus()
    symbol_list = ["AAPL"]
    data_handler = CSVDataHandler(event_bus, str(csv_dir), symbol_list)
    start_date = pd.Timestamp('2023-01-01')
    portfolio = Portfolio(data_handler, event_bus, start_date, initial_capital=100000.0)

    # Simulate a few timeindex updates
    data_handler.update_bars()
    portfolio.update_timeindex(event_bus.get())
    data_handler.update_bars()
    portfolio.update_timeindex(event_bus.get())
    data_handler.update_bars()
    portfolio.update_timeindex(event_bus.get())

    portfolio.create_equity_curve_dataframe()
    assert "equity_curve" in portfolio.equity_curve.columns
    assert len(portfolio.equity_curve) == 4 # Initial + 3 updates
    assert portfolio.equity_curve.iloc[0]['total'] == 100000.0
    assert portfolio.equity_curve.iloc[-1]['equity_curve'] == 100000.0 # No trades, so equity curve should be flat