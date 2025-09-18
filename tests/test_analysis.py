import unittest
import pandas as pd
import os
import shutil
from unittest.mock import patch
from analysis.data_manager import DataManager

class TestDataManager(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        """Set up dummy data files for all tests."""
        cls.data_dir = 'tests/data'
        os.makedirs(cls.data_dir, exist_ok=True)
        
        # 1-day data for basic tests
        cls.csv_path_1d = os.path.join(cls.data_dir, 'TEST.csv')
        data_1d = {
            'Date': ['2023-01-02', '2023-01-03', '2023-01-04', '2023-01-05', '2023-01-06'],
            'Open': [100, 101, 102, 104, 103],
            'High': [102, 103, 105, 104, 106],
            'Low': [99, 100, 101, 102, 103],
            'Close': [101, 102, 104, 103, 105],
            'Volume': [1000, 1200, 1500, 1300, 1600]
        }
        pd.DataFrame(data_1d).to_csv(cls.csv_path_1d, index=False)

        # 1-minute data for resampling tests
        cls.csv_path_1m = os.path.join(cls.data_dir, 'TEST_1M.csv')
        data_1m = {
            'Date': pd.to_datetime(['2023-01-01 00:00:00', '2023-01-01 00:01:00', '2023-01-01 00:02:00', '2023-01-01 00:03:00', '2023-01-01 00:04:00',
                               '2023-01-01 00:05:00', '2023-01-01 00:06:00', '2023-01-01 00:07:00', '2023-01-01 00:08:00', '2023-01-01 00:09:00']),
            'Open': [1.1, 1.1002, 1.1008, 1.101, 1.1014, 1.1018, 1.102, 1.1023, 1.1028, 1.1032],
            'High': [1.1005, 1.101, 1.1012, 1.1015, 1.102, 1.1022, 1.1025, 1.103, 1.1035, 1.1038],
            'Low': [1.0995, 1.1001, 1.1006, 1.1009, 1.1013, 1.1016, 1.1019, 1.1022, 1.1027, 1.1031],
            'Close': [1.1002, 1.1008, 1.101, 1.1014, 1.1018, 1.102, 1.1023, 1.1028, 1.1032, 1.1036],
            'Volume': [100, 120, 80, 150, 200, 110, 90, 130, 180, 220]
        }
        pd.DataFrame(data_1m).to_csv(cls.csv_path_1m, index=False)

    def setUp(self):
        """Create a temporary cache and data directory for each test."""
        self.cache_dir = 'tests/temp_cache'
        self.data_dir_temp = 'tests/temp_data'
        os.makedirs(self.cache_dir, exist_ok=True)
        os.makedirs(self.data_dir_temp, exist_ok=True)
        # Copy dummy files to temp data dir
        shutil.copy(self.csv_path_1d, os.path.join(self.data_dir_temp, 'TEST.csv'))
        shutil.copy(self.csv_path_1m, os.path.join(self.data_dir_temp, 'TEST_1M.csv'))

    def tearDown(self):
        """Remove the temporary cache and data directories after each test."""
        shutil.rmtree(self.cache_dir)
        shutil.rmtree(self.data_dir_temp)

    def test_get_data_full_day(self):
        """Test loading full 1-day data file."""
        dm = DataManager(data_path=self.data_dir_temp, cache_path=self.cache_dir)
        df = dm.get_data('TEST', timeframe='1d') # Should load TEST.csv and resample
        self.assertIsNotNone(df)
        self.assertEqual(len(df), 5)

    def test_resampling_1m_to_5m(self):
        """Test resampling 1-minute data to 5-minute timeframe."""
        dm = DataManager(data_path=self.data_dir_temp, cache_path=self.cache_dir)
        df_5m = dm.get_data('TEST_1M', timeframe='5T')

        self.assertIsNotNone(df_5m)
        self.assertEqual(len(df_5m), 2)

        # Verify first 5-min bar (00:00 to 00:04)
        first_bar = df_5m.iloc[0]
        self.assertEqual(first_bar['Open'], 1.1)
        self.assertAlmostEqual(first_bar['High'], 1.102)
        self.assertEqual(first_bar['Low'], 1.0995)
        self.assertAlmostEqual(first_bar['Close'], 1.1018)
        self.assertEqual(first_bar['Volume'], 650)
        self.assertEqual(first_bar.name, pd.to_datetime('2023-01-01 00:00:00').tz_localize('UTC'))

        # Verify second 5-min bar (00:05 to 00:09)
        second_bar = df_5m.iloc[1]
        self.assertEqual(second_bar['Open'], 1.1018)
        self.assertAlmostEqual(second_bar['High'], 1.1038)
        self.assertEqual(second_bar['Low'], 1.1016)
        self.assertAlmostEqual(second_bar['Close'], 1.1036)
        self.assertEqual(second_bar['Volume'], 730)
        self.assertEqual(second_bar.name, pd.to_datetime('2023-01-01 00:05:00').tz_localize('UTC'))

    def test_cache_creation_for_resampled_data(self):
        """Test that a cache file is created for resampled data."""
        dm = DataManager(data_path=self.data_dir_temp, cache_path=self.cache_dir)
        cache_file = os.path.join(self.cache_dir, 'TEST_1M_5T.parquet')
        
        self.assertFalse(os.path.exists(cache_file))
        dm.get_data('TEST_1M', timeframe='5T')
        self.assertTrue(os.path.exists(cache_file))

    def test_cache_usage_for_resampled_data(self):
        """Test that the cache is used for resampled data on the second load."""
        dm = DataManager(data_path=self.data_dir_temp, cache_path=self.cache_dir)
        
        # First call, should use read_csv and create the cache
        df_first = dm.get_data('TEST_1M', timeframe='5T')
        self.assertIsNotNone(df_first)

        # Patch read_csv and call again
        with patch('pandas.read_csv') as mock_read_csv:
            df_second = dm.get_data('TEST_1M', timeframe='5T')
            # Second call, should use the cache and not call read_csv
            mock_read_csv.assert_not_called()
        
        self.assertIsNotNone(df_second)
        self.assertEqual(len(df_second), 2)

    def test_get_data_not_found(self):
        """Test trying to load a non-existent file."""
        dm = DataManager(data_path=self.data_dir_temp, cache_path=self.cache_dir)
        df = dm.get_data('NONEXISTENT', timeframe='1d')
        self.assertIsNone(df)

if __name__ == '__main__':
    unittest.main()
