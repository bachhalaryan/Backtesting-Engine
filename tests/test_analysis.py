import unittest
import pandas as pd
import os
import shutil
from unittest.mock import patch
from analysis.data_manager import DataManager

class TestDataManager(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        """Set up a dummy data file for all tests."""
        cls.data_dir = 'tests/data'
        # This directory and its contents are now permanent and part of the repo
        os.makedirs(cls.data_dir, exist_ok=True)
        
        cls.csv_path = os.path.join(cls.data_dir, 'TEST_1d.csv')
        if not os.path.exists(cls.csv_path):
            data = {
                'Date': ['2023-01-02', '2023-01-03', '2023-01-04', '2023-01-05', '2023-01-06'],
                'Open': [100, 101, 102, 104, 103],
                'High': [102, 103, 105, 104, 106],
                'Low': [99, 100, 101, 102, 103],
                'Close': [101, 102, 104, 103, 105],
                'Volume': [1000, 1200, 1500, 1300, 1600]
            }
            df = pd.DataFrame(data)
            df.to_csv(cls.csv_path, index=False)

    def setUp(self):
        """Create a temporary cache directory for each test."""
        self.cache_dir = 'tests/temp_cache'
        os.makedirs(self.cache_dir, exist_ok=True)

    def tearDown(self):
        """Remove the temporary cache directory after each test."""
        shutil.rmtree(self.cache_dir)

    def test_get_data_full(self):
        """Test loading the full data file."""
        dm = DataManager(data_path=self.data_dir, cache_path=self.cache_dir)
        df = dm.get_data('TEST', timeframe='1d')
        self.assertIsNotNone(df)
        self.assertEqual(len(df), 5)
        self.assertTrue(pd.api.types.is_datetime64_any_dtype(df.index))

    def test_get_data_with_date_range(self):
        """Test loading data with a start and end date."""
        dm = DataManager(data_path=self.data_dir, cache_path=self.cache_dir)
        df = dm.get_data('TEST', start_date='2023-01-03', end_date='2023-01-05', timeframe='1d')
        self.assertIsNotNone(df)
        self.assertEqual(len(df), 3)
        self.assertEqual(df.index.min(), pd.to_datetime('2023-01-03'))
        self.assertEqual(df.index.max(), pd.to_datetime('2023-01-05'))

    def test_get_data_not_found(self):
        """Test trying to load a non-existent file."""
        dm = DataManager(data_path=self.data_dir, cache_path=self.cache_dir)
        df = dm.get_data('NONEXISTENT', timeframe='1d')
        self.assertIsNone(df)

    def test_cache_creation(self):
        """Test that a cache file is created after the first load."""
        dm = DataManager(data_path=self.data_dir, cache_path=self.cache_dir)
        cache_file = os.path.join(self.cache_dir, 'TEST_1d.parquet')
        
        self.assertFalse(os.path.exists(cache_file))
        dm.get_data('TEST', timeframe='1d')
        self.assertTrue(os.path.exists(cache_file))

    @patch('pandas.read_csv')
    def test_cache_usage(self, mock_read_csv):
        """Test that the cache is used on the second load."""
        dm = DataManager(data_path=self.data_dir, cache_path=self.cache_dir)
        
        # Configure the mock to return a dummy DataFrame
        dummy_df = pd.DataFrame({
            'Date': pd.to_datetime(['2023-01-02', '2023-01-03', '2023-01-04', '2023-01-05', '2023-01-06']),
            'Open': [100, 101, 102, 104, 103],
        }).set_index('Date')
        mock_read_csv.return_value = dummy_df

        # First call, should use read_csv and create the cache
        dm.get_data('TEST', timeframe='1d')
        
        # Reset the mock to clear the record of the first call
        mock_read_csv.reset_mock()

        # Second call, should use the cache and not call read_csv
        df = dm.get_data('TEST', timeframe='1d')

        mock_read_csv.assert_not_called()
        self.assertIsNotNone(df)
        self.assertEqual(len(df), 5)

if __name__ == '__main__':
    unittest.main()
