
import pytest
import os
import sys
import pandas as pd

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from event_bus import EventBus
from data_handler import CSVDataHandler

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
"""
    (csv_dir / "GOOG.csv").write_text(goog_csv_content)

    return csv_dir

def test_get_bars_all_data(setup_csv_data):
    csv_dir = setup_csv_data
    event_bus = EventBus()
    data_handler = CSVDataHandler(event_bus, str(csv_dir), ["AAPL"])

    # Simulate backtest progression
    for _ in range(10):
        data_handler.update_bars()

    historical_data = data_handler.get_bars("AAPL")
    assert isinstance(historical_data, pd.DataFrame)
    assert len(historical_data) == 10 # All 10 rows should be returned
    assert historical_data.index[0] == pd.Timestamp('2023-01-01')
    assert historical_data.index[-1] == pd.Timestamp('2023-01-10')

def test_get_bars_with_N(setup_csv_data):
    csv_dir = setup_csv_data
    event_bus = EventBus()
    data_handler = CSVDataHandler(event_bus, str(csv_dir), ["AAPL"])

    # Simulate backtest progression
    for _ in range(10):
        data_handler.update_bars()

    historical_data = data_handler.get_bars("AAPL", N=3)
    assert isinstance(historical_data, pd.DataFrame)
    assert len(historical_data) == 3
    assert historical_data.index[0] == pd.Timestamp('2023-01-08')
    assert historical_data.index[-1] == pd.Timestamp('2023-01-10')

def test_get_bars_non_existent_symbol(setup_csv_data):
    csv_dir = setup_csv_data
    event_bus = EventBus()
    data_handler = CSVDataHandler(event_bus, str(csv_dir), ["AAPL"])

    historical_data = data_handler.get_bars("NONEXISTENT")
    assert isinstance(historical_data, pd.DataFrame)
    assert historical_data.empty

def test_get_bars_multiple_symbols(setup_csv_data):
    csv_dir = setup_csv_data
    event_bus = EventBus()
    data_handler = CSVDataHandler(event_bus, str(csv_dir), ["AAPL", "GOOG"])

    # Simulate backtest progression
    for _ in range(10):
        data_handler.update_bars()

    aapl_data = data_handler.get_bars("AAPL", N=2)
    assert len(aapl_data) == 2
    assert aapl_data.index[0] == pd.Timestamp('2023-01-09')

    goog_data = data_handler.get_bars("GOOG")
    assert len(goog_data) == 10 # GOOG data will be reindexed to match AAPL length
    assert goog_data.index[0] == pd.Timestamp('2023-01-01')
