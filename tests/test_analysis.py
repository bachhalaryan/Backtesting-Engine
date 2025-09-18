import unittest
import pandas as pd
import os
from analysis.data_manager import DataManager

class TestDataManager(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        """Set up a dummy data file for testing."""
        cls.data_dir = 'tests/data'
        os.makedirs(cls.data_dir, exist_ok=True)
        
        cls.csv_path = os.path.join(cls.data_dir, 'TEST_1d.csv')
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

    def test_get_data_full(self):
        """Test loading the full data file."""
        dm = DataManager(data_path=self.data_dir)
        df = dm.get_data('TEST', timeframe='1d')
        self.assertIsNotNone(df)
        self.assertEqual(len(df), 5)
        self.assertTrue(pd.api.types.is_datetime64_any_dtype(df.index))

    def test_get_data_with_date_range(self):
        """Test loading data with a start and end date."""
        dm = DataManager(data_path=self.data_dir)
        df = dm.get_data('TEST', start_date='2023-01-03', end_date='2023-01-05', timeframe='1d')
        self.assertIsNotNone(df)
        self.assertEqual(len(df), 3)
        self.assertEqual(df.index.min(), pd.to_datetime('2023-01-03'))
        self.assertEqual(df.index.max(), pd.to_datetime('2023-01-05'))

    def test_get_data_not_found(self):
        """Test trying to load a non-existent file."""
        dm = DataManager(data_path=self.data_dir)
        df = dm.get_data('NONEXISTENT', timeframe='1d')
        self.assertIsNone(df)

if __name__ == '__main__':
    unittest.main()
