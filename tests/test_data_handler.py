import pytest
import pandas as pd
import os
import shutil
from unittest.mock import MagicMock
from data_handler import CSVDataHandler

# --- Fixtures for Test Data ---

@pytest.fixture
def tmp_csv_dir(tmp_path):
    """Provides a temporary directory for CSV files and ensures it's clean."""
    path = tmp_path / "data"
    path.mkdir()
    yield path
    # Teardown: pytest's tmp_path handles cleanup automatically

@pytest.fixture
def dummy_daily_df():
    """Provides a dummy DataFrame with daily data."""
    data = {
        'datetime': pd.to_datetime(['2023-01-01', '2023-01-02', '2023-01-03', '2023-01-04', '2023-01-05']),
        'open': [100, 101, 102, 103, 104],
        'high': [105, 106, 107, 108, 109],
        'low': [99, 100, 101, 102, 103],
        'close': [104, 105, 106, 107, 108],
        'volume': [1000, 1100, 1200, 1300, 1400]
    }
    df = pd.DataFrame(data)
    df.set_index('datetime', inplace=True)
    return df

@pytest.fixture
def dummy_minute_df():
    """Provides a dummy DataFrame with 1-minute data for a few hours."""
    start_time = pd.to_datetime('2023-01-01 09:00:00')
    end_time = pd.to_datetime('2023-01-01 12:00:00') # 3 hours of data
    time_range = pd.date_range(start=start_time, end=end_time, freq='1min')

    data = {
        'datetime': time_range,
        'open': [100 + i * 0.1 for i in range(len(time_range))],
        'high': [100 + i * 0.1 + 0.5 for i in range(len(time_range))],
        'low': [100 + i * 0.1 - 0.5 for i in range(len(time_range))],
        'close': [100 + i * 0.1 + 0.1 for i in range(len(time_range))],
        'volume': [100 + i * 10 for i in range(len(time_range))]
    }
    df = pd.DataFrame(data)
    df.set_index('datetime', inplace=True)
    return df

# --- Fixtures for Data Handlers ---

@pytest.fixture
def daily_data_handler(tmp_csv_dir, dummy_daily_df):
    """Provides a CSVDataHandler initialized with daily data."""
    dummy_daily_df.to_csv(tmp_csv_dir / "AAPL.csv")
    events = MagicMock()
    handler = CSVDataHandler(events, str(tmp_csv_dir), ['AAPL'])
    handler.current_time = dummy_daily_df.index[-1] # Set current_time for get_bars
    return handler

@pytest.fixture
def minute_data_handler(tmp_csv_dir, dummy_minute_df):
    """Provides a CSVDataHandler initialized with 1-minute data."""
    dummy_minute_df.to_csv(tmp_csv_dir / "AAPL.csv")
    events = MagicMock()
    handler = CSVDataHandler(events, str(tmp_csv_dir), ['AAPL'])
    handler.current_time = dummy_minute_df.index[-1] # Set current_time for get_bars
    return handler

# --- Tests ---

def test_get_bars_all(minute_data_handler, dummy_minute_df):
    bars = minute_data_handler.get_bars('AAPL')
    assert len(bars) == len(dummy_minute_df)

def test_get_bars_n(minute_data_handler, dummy_minute_df):
    bars = minute_data_handler.get_bars('AAPL', N=3)
    assert len(bars) == 3
    assert bars.index[0] == dummy_minute_df.index[-3]

def test_get_bars_start_date(minute_data_handler, dummy_minute_df):
    start_date = pd.Timestamp('2023-01-01 11:00:00')
    bars = minute_data_handler.get_bars('AAPL', start_date=start_date)
    expected_len = len(dummy_minute_df.loc[start_date:])
    assert len(bars) == expected_len
    assert bars.index[0] == start_date

def test_get_bars_end_date(minute_data_handler, dummy_minute_df):
    end_date = pd.Timestamp('2023-01-01 09:05:00')
    bars = minute_data_handler.get_bars('AAPL', end_date=end_date)
    expected_len = len(dummy_minute_df.loc[:end_date])
    assert len(bars) == expected_len
    assert bars.index[-1] == end_date

def test_get_bars_start_and_end_date(minute_data_handler, dummy_minute_df):
    start_date = pd.Timestamp('2023-01-01 10:00:00')
    end_date = pd.Timestamp('2023-01-01 10:30:00')
    bars = minute_data_handler.get_bars('AAPL', start_date=start_date, end_date=end_date)
    expected_len = len(dummy_minute_df.loc[start_date:end_date])
    assert len(bars) == expected_len
    assert bars.index[0] == start_date
    assert bars.index[-1] == end_date

def test_get_latest_bars(minute_data_handler, dummy_minute_df):
    bars = minute_data_handler.get_latest_bars('AAPL', N=2)
    assert len(bars) == 2
    assert bars.index[0] == dummy_minute_df.index[-2]

def test_csv_data_handler_filter_by_date_range(tmp_csv_dir, dummy_minute_df):
    start_date = pd.Timestamp('2023-01-01 10:00:00')
    end_date = pd.Timestamp('2023-01-01 10:05:00')
    dummy_minute_df.to_csv(tmp_csv_dir / "AAPL.csv") # Ensure CSV is written for this test
    data_handler = CSVDataHandler(
        MagicMock(), str(tmp_csv_dir), ['AAPL'],
        start_date=start_date,
        end_date=end_date
    )
    filtered_df = data_handler.symbol_data['AAPL']
    expected_df = dummy_minute_df.loc[start_date:end_date]
    assert len(filtered_df) == len(expected_df)
    assert filtered_df.index[0] == expected_df.index[0]
    assert filtered_df.index[-1] == expected_df.index[-1]

def test_csv_data_handler_filter_by_bars_from_end(tmp_csv_dir, dummy_minute_df):
    dummy_minute_df.to_csv(tmp_csv_dir / "AAPL.csv") # Ensure CSV is written for this test
    data_handler = CSVDataHandler(
        MagicMock(), str(tmp_csv_dir), ['AAPL'],
        bars_from_end=2
    )
    filtered_df = data_handler.symbol_data['AAPL']
    assert len(filtered_df) == 2
    assert filtered_df.index[0] == dummy_minute_df.index[-2]
    assert filtered_df.index[-1] == dummy_minute_df.index[-1]

def test_csv_data_handler_resampling_1H(tmp_csv_dir, dummy_minute_df):
    dummy_minute_df.to_csv(tmp_csv_dir / "AAPL.csv") # Ensure CSV is written for this test
    data_handler = CSVDataHandler(
        MagicMock(), str(tmp_csv_dir), ['AAPL'],
        resample_interval='1H'
    )
    resampled_df = data_handler.symbol_data['AAPL']
    
    # Expected number of 1-hour bars from 09:00 to 12:00 (inclusive of 12:00 if it's a full hour)
    # 09:00, 10:00, 11:00, 12:00 -> 4 bars
    assert len(resampled_df) == 4
    assert resampled_df.index[0] == pd.Timestamp('2023-01-01 09:00:00')
    assert resampled_df.index[-1] == pd.Timestamp('2023-01-01 12:00:00')

    # Verify OHLCV for the first resampled bar (09:00:00 to 09:59:00)
    # Open should be 09:00:00 open
    assert resampled_df.loc['2023-01-01 09:00:00']['open'] == pytest.approx(dummy_minute_df.loc['2023-01-01 09:00:00']['open'])
    # High should be max of 09:00:00 to 09:59:00 high
    assert resampled_df.loc['2023-01-01 09:00:00']['high'] == pytest.approx(dummy_minute_df.loc['2023-01-01 09:00:00':'2023-01-01 09:59:00']['high'].max())
    # Low should be min of 09:00:00 to 09:59:00 low
    assert resampled_df.loc['2023-01-01 09:00:00']['low'] == pytest.approx(dummy_minute_df.loc['2023-01-01 09:00:00':'2023-01-01 09:59:00']['low'].min())
    # Close should be 09:59:00 close
    assert resampled_df.loc['2023-01-01 09:00:00']['close'] == pytest.approx(dummy_minute_df.loc['2023-01-01 09:59:00']['close'])
    # Volume should be sum of 09:00:00 to 09:59:00 volume
    assert resampled_df.loc['2023-01-01 09:00:00']['volume'] == pytest.approx(dummy_minute_df.loc['2023-01-01 09:00:00':'2023-01-01 09:59:00']['volume'].sum())

def test_csv_data_handler_resampling_1D(tmp_csv_dir, dummy_minute_df):
    dummy_minute_df.to_csv(tmp_csv_dir / "AAPL.csv") # Ensure CSV is written for this test
    data_handler = CSVDataHandler(
        MagicMock(), str(tmp_csv_dir), ['AAPL'],
        resample_interval='1D'
    )
    resampled_df = data_handler.symbol_data['AAPL']

    # Expected number of 1-day bars (only one day in dummy data)
    assert len(resampled_df) == 1
    assert resampled_df.index[0] == pd.Timestamp('2023-01-01 00:00:00')

    # Verify OHLCV for the resampled bar
    assert resampled_df.loc['2023-01-01 00:00:00']['open'] == pytest.approx(dummy_minute_df['open'].iloc[0])
    assert resampled_df.loc['2023-01-01 00:00:00']['high'] == pytest.approx(dummy_minute_df['high'].max())
    assert resampled_df.loc['2023-01-01 00:00:00']['low'] == pytest.approx(dummy_minute_df['low'].min())
    assert resampled_df.loc['2023-01-01 00:00:00']['close'] == pytest.approx(dummy_minute_df['close'].iloc[-1])
    assert resampled_df.loc['2023-01-01 00:00:00']['volume'] == pytest.approx(dummy_minute_df['volume'].sum())