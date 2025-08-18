import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import unittest
import pandas as pd
from unittest.mock import MagicMock
from data_handler import CSVDataHandler

class TestCSVDataHandler(unittest.TestCase):
    def setUp(self):
        self.events = MagicMock()
        self.csv_dir = './data'
        self.symbol_list = ['AAPL']
        
        # Ensure the data directory exists
        os.makedirs(self.csv_dir, exist_ok=True)

        # Create a dummy CSV file for testing with 1-minute data
        start_time = pd.to_datetime('2023-01-01 09:00:00')
        end_time = pd.to_datetime('2023-01-01 12:00:00') # 3 hours of data
        time_range = pd.date_range(start=start_time, end=end_time, freq='1min')

        self.dummy_data = {
            'datetime': time_range,
            'open': [100 + i * 0.1 for i in range(len(time_range))],
            'high': [100 + i * 0.1 + 0.5 for i in range(len(time_range))],
            'low': [100 + i * 0.1 - 0.5 for i in range(len(time_range))],
            'close': [100 + i * 0.1 + 0.1 for i in range(len(time_range))],
            'volume': [100 + i * 10 for i in range(len(time_range))]
        }
        self.dummy_df = pd.DataFrame(self.dummy_data)
        self.dummy_df.set_index('datetime', inplace=True)
        
        # Create a dummy CSV file
        self.dummy_df.to_csv(f"{self.csv_dir}/AAPL.csv")

        self.data_handler = CSVDataHandler(self.events, self.csv_dir, self.symbol_list)
        self.data_handler.current_time = self.dummy_df.index[-1]

    def test_get_bars_all(self):
        bars = self.data_handler.get_bars('AAPL')
        self.assertEqual(len(bars), len(self.dummy_df))

    def test_get_bars_n(self):
        bars = self.data_handler.get_bars('AAPL', N=3)
        self.assertEqual(len(bars), 3)
        self.assertEqual(bars.index[0], self.dummy_df.index[-3])

    def test_get_bars_start_date(self):
        start_date = pd.Timestamp('2023-01-01 11:00:00')
        bars = self.data_handler.get_bars('AAPL', start_date=start_date)
        expected_len = len(self.dummy_df.loc[start_date:])
        self.assertEqual(len(bars), expected_len)
        self.assertEqual(bars.index[0], start_date)

    def test_get_bars_end_date(self):
        end_date = pd.Timestamp('2023-01-01 09:05:00')
        bars = self.data_handler.get_bars('AAPL', end_date=end_date)
        expected_len = len(self.dummy_df.loc[:end_date])
        self.assertEqual(len(bars), expected_len)
        self.assertEqual(bars.index[-1], end_date)

    def test_get_bars_start_and_end_date(self):
        start_date = pd.Timestamp('2023-01-01 10:00:00')
        end_date = pd.Timestamp('2023-01-01 10:30:00')
        bars = self.data_handler.get_bars('AAPL', start_date=start_date, end_date=end_date)
        expected_len = len(self.dummy_df.loc[start_date:end_date])
        self.assertEqual(len(bars), expected_len)
        self.assertEqual(bars.index[0], start_date)
        self.assertEqual(bars.index[-1], end_date)

    def test_get_latest_bars(self):
        bars = self.data_handler.get_latest_bars('AAPL', N=2)
        self.assertEqual(len(bars), 2)
        self.assertEqual(bars.index[0], self.dummy_df.index[-2])

    def test_csv_data_handler_filter_by_date_range(self):
        start_date = pd.Timestamp('2023-01-01 10:00:00')
        end_date = pd.Timestamp('2023-01-01 10:05:00')
        data_handler = CSVDataHandler(
            self.events, self.csv_dir, self.symbol_list,
            start_date=start_date,
            end_date=end_date
        )
        # The data should be filtered upon initialization
        filtered_df = data_handler.symbol_data['AAPL']
        expected_df = self.dummy_df.loc[start_date:end_date]
        self.assertEqual(len(filtered_df), len(expected_df))
        self.assertEqual(filtered_df.index[0], expected_df.index[0])
        self.assertEqual(filtered_df.index[-1], expected_df.index[-1])

    def test_csv_data_handler_filter_by_bars_from_end(self):
        # Create a data handler with a specific bars_from_end filter
        data_handler = CSVDataHandler(
            self.events, self.csv_dir, self.symbol_list,
            bars_from_end=2
        )
        # The data should be filtered upon initialization
        filtered_df = data_handler.symbol_data['AAPL']
        self.assertEqual(len(filtered_df), 2)
        self.assertEqual(filtered_df.index[0], self.dummy_df.index[-2])
        self.assertEqual(filtered_df.index[-1], self.dummy_df.index[-1])

    def test_csv_data_handler_resampling_1H(self):
        # Create a data handler with 1-hour resampling
        data_handler = CSVDataHandler(
            self.events, self.csv_dir, self.symbol_list,
            resample_interval='1H'
        )
        resampled_df = data_handler.symbol_data['AAPL']
        
        # Expected number of 1-hour bars from 09:00 to 12:00 (inclusive of 12:00 if it's a full hour)
        # 09:00, 10:00, 11:00, 12:00 -> 4 bars
        self.assertEqual(len(resampled_df), 4)
        self.assertEqual(resampled_df.index[0], pd.Timestamp('2023-01-01 09:00:00'))
        self.assertEqual(resampled_df.index[-1], pd.Timestamp('2023-01-01 12:00:00'))

        # Verify OHLCV for the first resampled bar (09:00:00 to 09:59:00)
        # Open should be 09:00:00 open
        self.assertAlmostEqual(resampled_df.loc['2023-01-01 09:00:00']['open'], 100.0)
        # High should be max of 09:00:00 to 09:59:00 high
        self.assertAlmostEqual(resampled_df.loc['2023-01-01 09:00:00']['high'], self.dummy_df.loc['2023-01-01 09:00:00':'2023-01-01 09:59:00']['high'].max())
        # Low should be min of 09:00:00 to 09:59:00 low
        self.assertAlmostEqual(resampled_df.loc['2023-01-01 09:00:00']['low'], self.dummy_df.loc['2023-01-01 09:00:00':'2023-01-01 09:59:00']['low'].min())
        # Close should be 09:59:00 close
        self.assertAlmostEqual(resampled_df.loc['2023-01-01 09:00:00']['close'], self.dummy_df.loc['2023-01-01 09:59:00']['close'])
        # Volume should be sum of 09:00:00 to 09:59:00 volume
        self.assertAlmostEqual(resampled_df.loc['2023-01-01 09:00:00']['volume'], self.dummy_df.loc['2023-01-01 09:00:00':'2023-01-01 09:59:00']['volume'].sum())

    def test_csv_data_handler_resampling_1D(self):
        # Create a data handler with 1-day resampling
        data_handler = CSVDataHandler(
            self.events, self.csv_dir, self.symbol_list,
            resample_interval='1D'
        )
        resampled_df = data_handler.symbol_data['AAPL']

        # Expected number of 1-day bars (only one day in dummy data)
        self.assertEqual(len(resampled_df), 1)
        self.assertEqual(resampled_df.index[0], pd.Timestamp('2023-01-01 00:00:00'))

        # Verify OHLCV for the resampled bar
        self.assertAlmostEqual(resampled_df.loc['2023-01-01 00:00:00']['open'], self.dummy_df['open'].iloc[0])
        self.assertAlmostEqual(resampled_df.loc['2023-01-01 00:00:00']['high'], self.dummy_df['high'].max())
        self.assertAlmostEqual(resampled_df.loc['2023-01-01 00:00:00']['low'], self.dummy_df['low'].min())
        self.assertAlmostEqual(resampled_df.loc['2023-01-01 00:00:00']['close'], self.dummy_df['close'].iloc[-1])
        self.assertAlmostEqual(resampled_df.loc['2023-01-01 00:00:00']['volume'], self.dummy_df['volume'].sum())

if __name__ == '__main__':
    unittest.main()
