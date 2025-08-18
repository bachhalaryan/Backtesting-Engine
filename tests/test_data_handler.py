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
        
        # Create a dummy CSV file for testing
        self.dummy_data = {
            'datetime': pd.to_datetime(['2023-01-01', '2023-01-02', '2023-01-03', '2023-01-04', '2023-01-05']),
            'open': [100, 101, 102, 103, 104],
            'high': [105, 106, 107, 108, 109],
            'low': [99, 100, 101, 102, 103],
            'close': [104, 105, 106, 107, 108],
            'volume': [1000, 1100, 1200, 1300, 1400]
        }
        self.dummy_df = pd.DataFrame(self.dummy_data)
        self.dummy_df.set_index('datetime', inplace=True)
        
        # Create a dummy CSV file
        self.dummy_df.to_csv(f"{self.csv_dir}/AAPL.csv")

        self.data_handler = CSVDataHandler(self.events, self.csv_dir, self.symbol_list)
        self.data_handler.current_time = pd.to_datetime('2023-01-05')

    def test_get_bars_all(self):
        bars = self.data_handler.get_bars('AAPL')
        self.assertEqual(len(bars), 5)

    def test_get_bars_n(self):
        bars = self.data_handler.get_bars('AAPL', N=3)
        self.assertEqual(len(bars), 3)
        self.assertEqual(bars.index[0], pd.Timestamp('2023-01-03'))

    def test_get_bars_start_date(self):
        bars = self.data_handler.get_bars('AAPL', start_date='2023-01-03')
        self.assertEqual(len(bars), 3)
        self.assertEqual(bars.index[0], pd.Timestamp('2023-01-03'))

    def test_get_bars_end_date(self):
        bars = self.data_handler.get_bars('AAPL', end_date='2023-01-03')
        self.assertEqual(len(bars), 3)
        self.assertEqual(bars.index[-1], pd.Timestamp('2023-01-03'))

    def test_get_bars_start_and_end_date(self):
        bars = self.data_handler.get_bars('AAPL', start_date='2023-01-02', end_date='2023-01-04')
        self.assertEqual(len(bars), 3)
        self.assertEqual(bars.index[0], pd.Timestamp('2023-01-02'))
        self.assertEqual(bars.index[-1], pd.Timestamp('2023-01-04'))

    def test_get_latest_bars(self):
        bars = self.data_handler.get_latest_bars('AAPL', N=2)
        self.assertEqual(len(bars), 2)
        self.assertEqual(bars.index[0], pd.Timestamp('2023-01-04'))

    def test_csv_data_handler_filter_by_date_range(self):
        # Create a data handler with a specific date range filter
        data_handler = CSVDataHandler(
            self.events, self.csv_dir, self.symbol_list,
            start_date=pd.Timestamp('2023-01-02'),
            end_date=pd.Timestamp('2023-01-04')
        )
        # The data should be filtered upon initialization
        filtered_df = data_handler.symbol_data['AAPL']
        self.assertEqual(len(filtered_df), 3)
        self.assertEqual(filtered_df.index[0], pd.Timestamp('2023-01-02'))
        self.assertEqual(filtered_df.index[-1], pd.Timestamp('2023-01-04'))

    def test_csv_data_handler_filter_by_bars_from_end(self):
        # Create a data handler with a specific bars_from_end filter
        data_handler = CSVDataHandler(
            self.events, self.csv_dir, self.symbol_list,
            bars_from_end=2
        )
        # The data should be filtered upon initialization
        filtered_df = data_handler.symbol_data['AAPL']
        self.assertEqual(len(filtered_df), 2)
        self.assertEqual(filtered_df.index[0], pd.Timestamp('2023-01-04'))
        self.assertEqual(filtered_df.index[-1], pd.Timestamp('2023-01-05'))

if __name__ == '__main__':
    unittest.main()
