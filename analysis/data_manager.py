import pandas as pd
from typing import List, Optional, Union
import os

class DataManager:
    """
    Manages loading, processing, and accessing financial data for analysis.
    """

    def __init__(self, data_path: str = './data', cache_path: str = './cache'):
        """
        Initializes the DataManager.

        Args:
            data_path (str): The base directory where data is stored.
            cache_path (str): The directory to store cached data.
        """
        self.data_path = data_path
        self.cache_path = cache_path
        os.makedirs(self.cache_path, exist_ok=True)
        # In the future, we can add connections to databases or APIs here.

    def get_data(
        self,
        symbol: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        timeframe: str = '1d',
    ) -> Optional[pd.DataFrame]:
        """
        Loads data for a given symbol and timeframe, using a cache to speed up
        subsequent loads.

        The method first checks for a cached Parquet file. If not found, it
        loads from the source CSV and creates a cache for future use.

        Args:
            symbol (str): The ticker symbol to load (e.g., 'AAPL').
            start_date (Optional[str]): The start date in 'YYYY-MM-DD' format.
            end_date (Optional[str]): The end date in 'YYYY-MM-DD' format.
            timeframe (str): The data timeframe (e.g., '1d', '1h', '1m').

        Returns:
            Optional[pd.DataFrame]: A DataFrame with the loaded data, or None if not found.
        """
        cache_file = f"{self.cache_path}/{symbol.upper()}_{timeframe}.parquet"
        
        df = None
        # 1. Try loading from cache
        if os.path.exists(cache_file):
            df = pd.read_parquet(cache_file)
        
        # 2. If cache miss, load from source
        else:
            source_file = f"{self.data_path}/{symbol.upper()}_{timeframe}.csv"
            try:
                df = pd.read_csv(source_file, index_col='Date', parse_dates=True)
                # Save to cache for next time
                df.to_parquet(cache_file)
            except FileNotFoundError:
                print(f"Data file not found: {source_file}")
                return None

        # 3. Filter by date range
        if df is not None:
            if start_date:
                df = df[df.index >= pd.to_datetime(start_date)]
            if end_date:
                df = df[df.index <= pd.to_datetime(end_date)]

        return df
