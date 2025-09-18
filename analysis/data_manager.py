import pandas as pd
from typing import List, Optional, Union
import os

class DataManager:
    """
    Manages loading, processing, and accessing financial data for analysis.
    This manager reads 1-minute data and can resample it to any specified timeframe.
    """

    def __init__(self, data_path: str = './data', cache_path: str = './cache'):
        """
        Initializes the DataManager.

        Args:
            data_path (str): The base directory where 1-minute CSV data is stored.
            cache_path (str): The directory to store cached (and resampled) data.
        """
        self.data_path = data_path
        self.cache_path = cache_path
        os.makedirs(self.cache_path, exist_ok=True)
        os.makedirs(self.data_path, exist_ok=True)

    def _resample_data(self, df: pd.DataFrame, timeframe: str) -> pd.DataFrame:
        """
        Resamples 1-minute data to a larger timeframe.
        """
        if df.index.tz is None:
            df.index = df.index.tz_localize('UTC')
        else:
            df.index = df.index.tz_convert('UTC')

        ohlc = {
            'Open': 'first',
            'High': 'max',
            'Low': 'min',
            'Close': 'last',
            'Volume': 'sum'
        }
        
        # Use 'base' parameter to align the resampling to the start of the interval
        resampled_df = df.resample(timeframe, label='left', closed='left').agg(ohlc).dropna()
        
        return resampled_df

    def get_data(
        self,
        symbol: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        timeframe: str = '1d',
    ) -> Optional[pd.DataFrame]:
        """
        Loads data for a given symbol and timeframe. It first checks the cache
        for resampled data. If not found, it loads the base 1-minute data,
        resamples it, caches it, and then returns the requested data.

        Args:
            symbol (str): The ticker symbol to load (e.g., 'EURUSD').
            start_date (Optional[str]): The start date in 'YYYY-MM-DD' format.
            end_date (Optional[str]): The end date in 'YYYY-MM-DD' format.
            timeframe (str): The target data timeframe (e.g., '5m', '1h', '1d').

        Returns:
            Optional[pd.DataFrame]: A DataFrame with the loaded and resampled data, or None if not found.
        """
        cache_file = f"{self.cache_path}/{symbol.upper()}_{timeframe}.parquet"
        
        # 1. Try loading from cache
        if os.path.exists(cache_file):
            df = pd.read_parquet(cache_file)
        else:
            # 2. If cache miss, load 1-minute source data
            source_file = f"{self.data_path}/{symbol.upper()}.csv"
            if not os.path.exists(source_file):
                print(f"Source file not found: {source_file}")
                return None
            
            try:
                df_1m = pd.read_csv(source_file, index_col='Date', parse_dates=True)
                
                # 3. Resample the data
                if timeframe == '1m':
                    df = df_1m
                else:
                    df = self._resample_data(df_1m, timeframe)
                
                # 4. Save the resampled data to cache
                df.to_parquet(cache_file)

            except Exception as e:
                print(f"Error processing source file {source_file}: {e}")
                return None

        # 5. Filter by date range
        if df is not None and not df.empty:
            if start_date:
                df = df[df.index >= pd.to_datetime(start_date).tz_localize('UTC')]
            if end_date:
                df = df[df.index <= pd.to_datetime(end_date).tz_localize('UTC')]
        
        return df
