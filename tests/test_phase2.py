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
    def get_latest_bars(self, symbol, N=1):
        data = [(pd.Timestamp('2023-01-01'), {'open': 100, 'high': 101, 'low': 99, 'close': 100.5, 'volume': 100000})]
        df = pd.DataFrame([x[1] for x in data], index=[x[0] for x in data])
        df.index.name = 'datetime'
        return df.tail(N)

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

    goog_csv_content = """
datetime,open,high,low,close,volume
2023-01-01,200.00,201.00,199.00,200.50,200000
2023-01-02,200.50,202.00,200.00,201.50,240000
2023-01-03,201.50,203.00,201.00,202.50,300000
2023-01-04,202.50,204.00,202.00,203.50,320000
2023-01-05,203.50,205.00,203.00,204.50,350000
2023-01-06,204.50,206.00,204.00,205.50,380000
2023-01-07,205.50,207.00,205.00,206.50,400000
2023-01-08,206.50,208.00,206.00,207.50,420000
2023-01-09,207.50,209.00,207.00,208.50,450000
2023-01-10,208.50,210.00,208.00,209.50,480000
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

    # Update bars for all 10 days
    for i in range(10):
        handler.update_bars()
        assert not event_bus.empty()
        event = event_bus.get()
        assert event.type == 'MARKET'
        assert len(handler.latest_symbol_data["AAPL"]) == i + 1
        assert handler.latest_symbol_data["AAPL"][i][0] == pd.Timestamp(f'2023-01-{i+1:02d}')

    # After all bars are processed, continue_backtest should be False
    handler.update_bars() # One more call to trigger StopIteration
    assert not handler.continue_backtest
    assert event_bus.empty() # No new market event should be put

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
    assert latest_bar.index[0] == pd.Timestamp('2023-01-03')

    latest_two_bars = handler.get_latest_bars("AAPL", N=2)
    assert len(latest_two_bars) == 2
    assert latest_two_bars.index[0] == pd.Timestamp('2023-01-02')
    assert latest_two_bars.index[1] == pd.Timestamp('2023-01-03')

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

def test_portfolio_position_sizing(setup_csv_data):
    csv_dir = setup_csv_data
    event_bus = EventBus()
    symbol_list = ["AAPL"]
    data_handler = CSVDataHandler(event_bus, str(csv_dir), symbol_list)
    start_date = pd.Timestamp('2023-01-01')
    portfolio = Portfolio(data_handler, event_bus, start_date, initial_capital=100000.0)

    # Simulate a market event to get current price
    data_handler.update_bars()
    market_event = event_bus.get()
    portfolio.update_timeindex(market_event)

    # Test FIXED_SHARES sizing
    signal_event_fixed = SignalEvent(1, "AAPL", pd.Timestamp('2023-01-01'), 'LONG', 1.0, sizing_type='FIXED_SHARES', sizing_value=50)
    portfolio.update_signal(signal_event_fixed)
    order_event_fixed = event_bus.get()
    assert order_event_fixed.quantity == 50

    # Test PERCENT_EQUITY sizing (assuming 100.50 close price from MockBars)
    # 10% of 100000 capital = 10000.  10000 / 100.50 = 99.5 -> 99 shares
    signal_event_percent = SignalEvent(1, "AAPL", pd.Timestamp('2023-01-01'), 'LONG', 1.0, sizing_type='PERCENT_EQUITY', sizing_value=0.10)
    portfolio.update_signal(signal_event_percent)
    order_event_percent = event_bus.get()
    assert order_event_percent.quantity == int((100000.0 * 0.10) / data_handler.get_latest_bars("AAPL").iloc[-1]['close'])

    # Test FIXED_CAPITAL sizing
    # 5000 capital / 100.50 = 49.75 -> 49 shares
    signal_event_capital = SignalEvent(1, "AAPL", pd.Timestamp('2023-01-01'), 'LONG', 1.0, sizing_type='FIXED_CAPITAL', sizing_value=5000)
    portfolio.update_signal(signal_event_capital)
    order_event_capital = event_bus.get()
    assert order_event_capital.quantity == int(5000 / data_handler.get_latest_bars("AAPL").iloc[-1]['close'])

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

def test_portfolio_open_short_position(setup_csv_data):
    csv_dir = setup_csv_data
    event_bus = EventBus()
    symbol_list = ["AAPL"]
    data_handler = CSVDataHandler(event_bus, str(csv_dir), symbol_list)
    start_date = pd.Timestamp('2023-01-01')
    portfolio = Portfolio(data_handler, event_bus, start_date, initial_capital=100000.0)
    execution_handler = SimulatedExecutionHandler(event_bus, data_handler)

    # Simulate market event and update timeindex
    data_handler.update_bars()
    market_event = event_bus.get()
    portfolio.update_timeindex(market_event)

    # Simulate a sell order to open a short position
    order = OrderEvent("AAPL", "MKT", 100, "SELL")
    execution_handler.execute_order(order)
    execution_handler.process_immediate_order(order.order_id, market_event)
    fill_event = event_bus.get()
    portfolio.update_fill(fill_event)

    assert portfolio.current_positions['AAPL'] == -100
    assert portfolio.open_positions_details['AAPL']['quantity'] == 100
    assert portfolio.open_positions_details['AAPL']['direction'] == 'SHORT'
    assert not portfolio.closed_trades

def test_portfolio_close_short_position(setup_csv_data):
    csv_dir = setup_csv_data
    event_bus = EventBus()
    symbol_list = ["AAPL"]
    data_handler = CSVDataHandler(event_bus, str(csv_dir), symbol_list)
    start_date = pd.Timestamp('2023-01-01')
    portfolio = Portfolio(data_handler, event_bus, start_date, initial_capital=100000.0)
    execution_handler = SimulatedExecutionHandler(event_bus, data_handler)

    # Open short position
    data_handler.update_bars() # Day 1
    market_event_day1 = event_bus.get()
    portfolio.update_timeindex(market_event_day1)
    order_open = OrderEvent("AAPL", "MKT", 100, "SELL")
    execution_handler.execute_order(order_open)
    execution_handler.process_immediate_order(order_open.order_id, market_event_day1)
    fill_open = event_bus.get()
    portfolio.update_fill(fill_open)

    # Close short position on Day 2
    data_handler.update_bars() # Day 2
    market_event_day2 = event_bus.get()
    portfolio.update_timeindex(market_event_day2)
    order_close = OrderEvent("AAPL", "MKT", 100, "BUY")
    execution_handler.execute_order(order_close)
    execution_handler.process_immediate_order(order_close.order_id, market_event_day2)
    fill_close = event_bus.get()
    portfolio.update_fill(fill_close)

    assert portfolio.current_positions['AAPL'] == 0
    assert not portfolio.open_positions_details
    assert len(portfolio.closed_trades) == 1
    trade = portfolio.closed_trades[0]
    assert trade['direction'] == 'SHORT'
    assert trade['quantity'] == 100
    assert trade['entry_price'] == pytest.approx(100.00) # Day 1 open
    assert trade['exit_price'] == pytest.approx(100.50) # Day 2 open
    assert trade['pnl'] == pytest.approx((100.00 - 100.50) * 100 - (fill_open.commission + fill_close.commission))

def test_portfolio_partial_close_long_position(setup_csv_data):
    csv_dir = setup_csv_data
    event_bus = EventBus()
    symbol_list = ["AAPL"]
    data_handler = CSVDataHandler(event_bus, str(csv_dir), symbol_list)
    start_date = pd.Timestamp('2023-01-01')
    portfolio = Portfolio(data_handler, event_bus, start_date, initial_capital=100000.0)
    execution_handler = SimulatedExecutionHandler(event_bus, data_handler)

    # Open long position
    data_handler.update_bars() # Day 1
    market_event_day1 = event_bus.get()
    portfolio.update_timeindex(market_event_day1)
    order_open = OrderEvent("AAPL", "MKT", 100, "BUY")
    execution_handler.execute_order(order_open)
    execution_handler.process_immediate_order(order_open.order_id, market_event_day1)
    fill_open = event_bus.get()
    portfolio.update_fill(fill_open)

    # Partial close on Day 2
    data_handler.update_bars() # Day 2
    market_event_day2 = event_bus.get()
    portfolio.update_timeindex(market_event_day2)
    order_partial_close = OrderEvent("AAPL", "MKT", 40, "SELL")
    execution_handler.execute_order(order_partial_close)
    execution_handler.process_immediate_order(order_partial_close.order_id, market_event_day2)
    fill_partial_close = event_bus.get()
    portfolio.update_fill(fill_partial_close)

    assert portfolio.current_positions['AAPL'] == 60
    assert portfolio.open_positions_details['AAPL']['quantity'] == 60
    assert len(portfolio.closed_trades) == 1
    trade = portfolio.closed_trades[0]
    assert trade['quantity'] == 40
    assert trade['direction'] == 'LONG'
    assert trade['pnl'] == pytest.approx((100.50 - 100.00) * 40 - ((fill_open.commission/100)*40 + fill_partial_close.commission))

def test_portfolio_partial_close_short_position(setup_csv_data):
    csv_dir = setup_csv_data
    event_bus = EventBus()
    symbol_list = ["AAPL"]
    data_handler = CSVDataHandler(event_bus, str(csv_dir), symbol_list)
    start_date = pd.Timestamp('2023-01-01')
    portfolio = Portfolio(data_handler, event_bus, start_date, initial_capital=100000.0)
    execution_handler = SimulatedExecutionHandler(event_bus, data_handler)

    # Open short position
    data_handler.update_bars() # Day 1
    market_event_day1 = event_bus.get()
    portfolio.update_timeindex(market_event_day1)
    order_open = OrderEvent("AAPL", "MKT", 100, "SELL")
    execution_handler.execute_order(order_open)
    execution_handler.process_immediate_order(order_open.order_id, market_event_day1)
    fill_open = event_bus.get()
    portfolio.update_fill(fill_open)

    # Partial close on Day 2
    data_handler.update_bars() # Day 2
    market_event_day2 = event_bus.get()
    portfolio.update_timeindex(market_event_day2)
    order_partial_close = OrderEvent("AAPL", "MKT", 40, "BUY")
    execution_handler.execute_order(order_partial_close)
    execution_handler.process_immediate_order(order_partial_close.order_id, market_event_day2)
    fill_partial_close = event_bus.get()
    portfolio.update_fill(fill_partial_close)

    assert portfolio.current_positions['AAPL'] == -60
    assert portfolio.open_positions_details['AAPL']['quantity'] == 60
    assert len(portfolio.closed_trades) == 1
    trade = portfolio.closed_trades[0]
    assert trade['quantity'] == 40
    assert trade['direction'] == 'SHORT'
    assert trade['pnl'] == pytest.approx((100.00 - 100.50) * 40 - ((fill_open.commission/100)*40 + fill_partial_close.commission))

def test_portfolio_add_to_long_position_averaging(setup_csv_data):
    csv_dir = setup_csv_data
    event_bus = EventBus()
    symbol_list = ["AAPL"]
    data_handler = CSVDataHandler(event_bus, str(csv_dir), symbol_list)
    start_date = pd.Timestamp('2023-01-01')
    portfolio = Portfolio(data_handler, event_bus, start_date, initial_capital=100000.0)
    execution_handler = SimulatedExecutionHandler(event_bus, data_handler)

    # First buy (Day 1)
    data_handler.update_bars() # Day 1: Open=100.00
    market_event_day1 = event_bus.get()
    portfolio.update_timeindex(market_event_day1)
    buy_order1 = OrderEvent("AAPL", "MKT", 50, "BUY")
    execution_handler.execute_order(buy_order1)
    execution_handler.process_immediate_order(buy_order1.order_id, market_event_day1)
    fill_buy1 = event_bus.get()
    portfolio.update_fill(fill_buy1)

    # Second buy (Day 2)
    data_handler.update_bars() # Day 2: Open=100.50
    market_event_day2 = event_bus.get()
    portfolio.update_timeindex(market_event_day2)
    buy_order2 = OrderEvent("AAPL", "MKT", 50, "BUY")
    execution_handler.execute_order(buy_order2)
    execution_handler.process_immediate_order(buy_order2.order_id, market_event_day2)
    fill_buy2 = event_bus.get()
    portfolio.update_fill(fill_buy2)

    assert portfolio.current_positions['AAPL'] == 100
    assert portfolio.open_positions_details['AAPL']['quantity'] == 100
    # (50 * 100.00 + 50 * 100.50) / 100 = 100.25
    assert portfolio.open_positions_details['AAPL']['entry_price'] == pytest.approx(100.25)
    assert portfolio.open_positions_details['AAPL']['total_entry_commission'] == pytest.approx(fill_buy1.commission + fill_buy2.commission)
    assert not portfolio.closed_trades

def test_portfolio_add_to_short_position_averaging(setup_csv_data):
    csv_dir = setup_csv_data
    event_bus = EventBus()
    symbol_list = ["AAPL"]
    data_handler = CSVDataHandler(event_bus, str(csv_dir), symbol_list)
    start_date = pd.Timestamp('2023-01-01')
    portfolio = Portfolio(data_handler, event_bus, start_date, initial_capital=100000.0)
    execution_handler = SimulatedExecutionHandler(event_bus, data_handler)

    # First sell (Day 1)
    data_handler.update_bars() # Day 1: Open=100.00
    market_event_day1 = event_bus.get()
    portfolio.update_timeindex(market_event_day1)
    sell_order1 = OrderEvent("AAPL", "MKT", 50, "SELL")
    execution_handler.execute_order(sell_order1)
    execution_handler.process_immediate_order(sell_order1.order_id, market_event_day1)
    fill_sell1 = event_bus.get()
    portfolio.update_fill(fill_sell1)

    # Second sell (Day 2)
    data_handler.update_bars() # Day 2: Open=100.50
    market_event_day2 = event_bus.get()
    portfolio.update_timeindex(market_event_day2)
    sell_order2 = OrderEvent("AAPL", "MKT", 50, "SELL")
    execution_handler.execute_order(sell_order2)
    execution_handler.process_immediate_order(sell_order2.order_id, market_event_day2)
    fill_sell2 = event_bus.get()
    portfolio.update_fill(fill_sell2)

    assert portfolio.current_positions['AAPL'] == -100
    assert portfolio.open_positions_details['AAPL']['quantity'] == 100
    # (50 * 100.00 + 50 * 100.50) / 100 = 100.25
    assert portfolio.open_positions_details['AAPL']['entry_price'] == pytest.approx(100.25)
    assert portfolio.open_positions_details['AAPL']['total_entry_commission'] == pytest.approx(fill_sell1.commission + fill_sell2.commission)
    assert not portfolio.closed_trades

def test_portfolio_reverse_long_to_short(setup_csv_data):
    csv_dir = setup_csv_data
    event_bus = EventBus()
    symbol_list = ["AAPL"]
    data_handler = CSVDataHandler(event_bus, str(csv_dir), symbol_list)
    start_date = pd.Timestamp('2023-01-01')
    portfolio = Portfolio(data_handler, event_bus, start_date, initial_capital=100000.0)
    execution_handler = SimulatedExecutionHandler(event_bus, data_handler)

    # Open long position (Day 1)
    data_handler.update_bars() # Day 1: Open=100.00
    market_event_day1 = event_bus.get()
    portfolio.update_timeindex(market_event_day1)
    buy_order = OrderEvent("AAPL", "MKT", 50, "BUY")
    execution_handler.execute_order(buy_order)
    execution_handler.process_immediate_order(buy_order.order_id, market_event_day1)
    fill_buy = event_bus.get()
    portfolio.update_fill(fill_buy)

    # Sell more than held long (Day 2)
    data_handler.update_bars() # Day 2: Open=100.50
    market_event_day2 = event_bus.get()
    portfolio.update_timeindex(market_event_day2)
    sell_order = OrderEvent("AAPL", "MKT", 100, "SELL") # Sell 100, but only 50 held long
    execution_handler.execute_order(sell_order)
    execution_handler.process_immediate_order(sell_order.order_id, market_event_day2)
    fill_sell = event_bus.get()
    portfolio.update_fill(fill_sell)

    assert portfolio.current_positions['AAPL'] == -50 # 50 long - 100 sell = -50 short
    assert len(portfolio.closed_trades) == 1
    closed_trade = portfolio.closed_trades[0]
    assert closed_trade['quantity'] == 50 # Only the long position was closed
    assert closed_trade['direction'] == 'LONG'
    assert portfolio.open_positions_details['AAPL']['quantity'] == 50 # New short position
    assert portfolio.open_positions_details['AAPL']['direction'] == 'SHORT'
    assert portfolio.open_positions_details['AAPL']['entry_price'] == pytest.approx(100.50) # New short entry price

def test_portfolio_reverse_short_to_long(setup_csv_data):
    csv_dir = setup_csv_data
    event_bus = EventBus()
    symbol_list = ["AAPL"]
    data_handler = CSVDataHandler(event_bus, str(csv_dir), symbol_list)
    start_date = pd.Timestamp('2023-01-01')
    portfolio = Portfolio(data_handler, event_bus, start_date, initial_capital=100000.0)
    execution_handler = SimulatedExecutionHandler(event_bus, data_handler)

    # Open short position (Day 1)
    data_handler.update_bars() # Day 1: Open=100.00
    market_event_day1 = event_bus.get()
    portfolio.update_timeindex(market_event_day1)
    sell_order = OrderEvent("AAPL", "MKT", 50, "SELL")
    execution_handler.execute_order(sell_order)
    execution_handler.process_immediate_order(sell_order.order_id, market_event_day1)
    fill_sell = event_bus.get()
    portfolio.update_fill(fill_sell)

    # Buy more than held short (Day 2)
    data_handler.update_bars() # Day 2: Open=100.50
    market_event_day2 = event_bus.get()
    portfolio.update_timeindex(market_event_day2)
    buy_order = OrderEvent("AAPL", "MKT", 100, "BUY") # Buy 100, but only 50 held short
    execution_handler.execute_order(buy_order)
    execution_handler.process_immediate_order(buy_order.order_id, market_event_day2)
    fill_buy = event_bus.get()
    portfolio.update_fill(fill_buy)

    assert portfolio.current_positions['AAPL'] == 50 # -50 short + 100 buy = 50 long
    assert len(portfolio.closed_trades) == 1
    closed_trade = portfolio.closed_trades[0]
    assert closed_trade['quantity'] == 50 # Only the short position was closed
    assert closed_trade['direction'] == 'SHORT'
    assert portfolio.open_positions_details['AAPL']['quantity'] == 50 # New long position
    assert portfolio.open_positions_details['AAPL']['direction'] == 'LONG'
    assert portfolio.open_positions_details['AAPL']['entry_price'] == pytest.approx(100.50) # New long entry price

def test_buy_and_hold_strategy_advanced_orders(setup_csv_data):
    csv_dir = setup_csv_data
    event_bus = EventBus()
    symbol_list = ["AAPL"]
    data_handler = CSVDataHandler(event_bus, str(csv_dir), symbol_list)
    start_date = pd.Timestamp('2023-01-01')
    portfolio = Portfolio(data_handler, event_bus, start_date, initial_capital=100000.0)
    execution_handler = SimulatedExecutionHandler(event_bus, data_handler)
    strategy = BuyAndHoldStrategy("AAPL", event_bus, data_handler, portfolio, execution_handler)

    # Simulate market events and check generated signals
    # Bar 1: Initial Market Buy
    data_handler.update_bars()
    market_event = event_bus.get()
    strategy.calculate_signals(market_event)
    signal = event_bus.get()
    assert signal.type == 'SIGNAL'
    assert signal.signal_type == 'LONG'
    assert signal.order_type == 'MKT'
    assert signal.immediate_fill == False
    assert signal.sizing_value == 100

    # Bar 2: No signal
    data_handler.update_bars()
    market_event = event_bus.get()
    strategy.calculate_signals(market_event)
    assert event_bus.empty()

    # Bar 3: Limit Buy
    data_handler.update_bars()
    market_event = event_bus.get()
    strategy.calculate_signals(market_event)
    signal = event_bus.get()
    assert signal.type == 'SIGNAL'
    assert signal.signal_type == 'LONG'
    assert signal.order_type == 'LMT'
    assert signal.limit_price is not None
    assert signal.sizing_value == 50

    # Bar 4: No signal
    data_handler.update_bars()
    market_event = event_bus.get()
    strategy.calculate_signals(market_event)
    assert event_bus.empty()

    # Bar 5: Stop Sell
    data_handler.update_bars()
    market_event = event_bus.get()
    strategy.calculate_signals(market_event)
    signal = event_bus.get()
    assert signal.type == 'SIGNAL'
    assert signal.signal_type == 'EXIT'
    assert signal.order_type == 'STP'
    assert signal.stop_price is not None

    # Bar 6: No signal
    data_handler.update_bars()
    market_event = event_bus.get()
    strategy.calculate_signals(market_event)
    assert event_bus.empty()

    # Bar 7: Trailing Stop Sell
    data_handler.update_bars()
    market_event = event_bus.get()
    strategy.calculate_signals(market_event)
    signal = event_bus.get()
    assert signal.type == 'SIGNAL'
    assert signal.signal_type == 'EXIT'
    assert signal.order_type == 'TRAIL'
    assert signal.trail_price is not None

    # Bar 8: No signal
    data_handler.update_bars()
    market_event = event_bus.get()
    strategy.calculate_signals(market_event)
    assert event_bus.empty()

    # Bar 9: Immediate Fill Market Buy
    data_handler.update_bars()
    market_event = event_bus.get()
    strategy.calculate_signals(market_event)
    signal = event_bus.get()
    assert signal.type == 'SIGNAL'
    assert signal.signal_type == 'LONG'
    assert signal.order_type == 'MKT'
    assert signal.immediate_fill == True
    assert signal.sizing_value == 20

    # Bar 10: Final Exit Market Order
    data_handler.update_bars()
    market_event = event_bus.get()
    strategy.calculate_signals(market_event)
    signal = event_bus.get()
    assert signal.type == 'SIGNAL'
    assert signal.signal_type == 'EXIT'
    assert signal.order_type == 'MKT'
    assert signal.immediate_fill == False