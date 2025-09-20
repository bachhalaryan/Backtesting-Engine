import unittest
import pandas as pd
from analysis.timeseries import calculate_sma, calculate_ema, calculate_rsi, calculate_bollinger_bands, calculate_mid_price

class TestTimeSeriesAnalysis(unittest.TestCase):

    def setUp(self):
        # Create a dummy DataFrame for testing
        self.data = {
            'Date': pd.to_datetime([
                '2023-01-01', '2023-01-02', '2023-01-03', '2023-01-04', '2023-01-05',
                '2023-01-06', '2023-01-07', '2023-01-08', '2023-01-09', '2023-01-10',
                '2023-01-11', '2023-01-12', '2023-01-13', '2023-01-14', '2023-01-15',
                '2023-01-16', '2023-01-17', '2023-01-18', '2023-01-19', '2023-01-20',
            ]),
            'Close': [
                10, 11, 12, 13, 14, 15, 16, 17, 18, 19,
                20, 21, 22, 23, 24, 25, 26, 27, 28, 29,
            ]
        }
        self.df = pd.DataFrame(self.data).set_index('Date')

    def test_calculate_sma(self):
        sma = calculate_sma(self.df, window=5)
        self.assertIsInstance(sma, pd.Series)
        self.assertEqual(len(sma), len(self.df))
        self.assertTrue(sma.iloc[4] == 12.0) # (10+11+12+13+14)/5
        self.assertTrue(sma.iloc[9] == 17.0) # (15+16+17+18+19)/5
        self.assertTrue(sma.iloc[0:4].isnull().all()) # First 4 values should be NaN

    def test_calculate_ema(self):
        ema = calculate_ema(self.df, window=5)
        self.assertIsInstance(ema, pd.Series)
        self.assertEqual(len(ema), len(self.df))
        self.assertFalse(ema.isnull().all()) # EMA should not be all NaN
        # For a constantly increasing series, EMA should also be increasing (after initial NaNs)
        self.assertTrue(ema.dropna().is_monotonic_increasing)

    def test_calculate_rsi(self):
        rsi = calculate_rsi(self.df, window=14)
        self.assertIsInstance(rsi, pd.Series)
        self.assertEqual(len(rsi), len(self.df))
        self.assertTrue(rsi.iloc[0:13].isnull().all()) # First 13 values should be NaN
        # For a constantly increasing series, RSI should approach 100
        self.assertGreater(rsi.iloc[-1], 90) 

    def test_calculate_bollinger_bands(self):
        bb = calculate_bollinger_bands(self.df, window=20, window_dev=2)
        self.assertIsInstance(bb, pd.DataFrame)
        self.assertEqual(len(bb), len(self.df))
        self.assertIn('bb_bbm', bb.columns)
        self.assertIn('bb_bbh', bb.columns)
        self.assertIn('bb_bbl', bb.columns)
        self.assertTrue(bb.iloc[0:19].isnull().all().all()) # First 19 values should be NaN
        self.assertAlmostEqual(bb['bb_bbm'].iloc[-1], 19.5, places=3) # (10+..+29)/20

    def test_calculate_mid_price(self):
        df_with_ohlc = pd.DataFrame({
            'High': [10, 12, 14, 16, 18],
            'Low': [8, 10, 12, 14, 16]
        })
        mid_price = calculate_mid_price(df_with_ohlc)
        self.assertIsInstance(mid_price, pd.Series)
        self.assertEqual(len(mid_price), 5)
        self.assertTrue((mid_price == pd.Series([9.0, 11.0, 13.0, 15.0, 17.0])).all())

        # Test with missing columns
        df_missing_high = pd.DataFrame({'low': [1, 2, 3]})
        with self.assertRaises(ValueError):
            calculate_mid_price(df_missing_high)

        df_missing_low = pd.DataFrame({'high': [1, 2, 3]})
        with self.assertRaises(ValueError):
            calculate_mid_price(df_missing_low)

if __name__ == '__main__':
    unittest.main()
