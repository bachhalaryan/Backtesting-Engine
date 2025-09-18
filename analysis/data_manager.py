import pandas as pd
from typing import List, Optional, Union
import os
import yfinance as yf

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
        os.makedirs(self.data_path, exist_ok=True) # Ensure data directory exists

    def _fetch_data_from_api(
        self,
        symbol: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        timeframe: str = '1d',
    ) -> Optional[pd.DataFrame]:
        """
        Fetches historical data for a given symbol from Yahoo Finance.
        """
        if timeframe != '1d':
            print(f"Warning: yfinance only supports daily data for now. Timeframe {timeframe} will be ignored.")

        ticker = yf.Ticker(symbol)
        try:
            df = ticker.history(start=start_date, end=end_date)
            if not df.empty:
                df.index.name = 'Date'
                # Save to CSV for future direct loading
                source_file = f"{self.data_path}/{symbol.upper()}_{timeframe}.csv"
                df.to_csv(source_file)
                return df
            else:
                print(f"No data fetched from API for {symbol} between {start_date} and {end_date}")
                return None
        except Exception as e:
            print(f"Error fetching data from yfinance for {symbol}: {e}")
            return None

    def get_data(
        self,
        symbol: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        timeframe: str = '1d',
    ) -> Optional[pd.DataFrame]:
        """
        Loads data for a given symbol and timeframe, using a cache to speed up
        subsequent loads. If not found in cache or local CSV, fetches from API.

        Args:
            symbol (str): The ticker symbol to load (e.g., 'AAPL').
            start_date (Optional[str]): The start date in 'YYYY-MM-DD' format.
            end_date (Optional[str]): The end date in 'YYYY-MM-DD' format.
            timeframe (str): The data timeframe (e.g., '1d', '1h', '1m').

        Returns:
            Optional[pd.DataFrame]: A DataFrame with the loaded data, or None if not found.
        """
        cache_file = f"{self.cache_path}/{symbol.upper()}_{timeframe}.parquet"
        source_file = f"{self.data_path}/{symbol.upper()}_{timeframe}.csv"
        
        df = None
        # 1. Try loading from cache
        if os.path.exists(cache_file):
            df = pd.read_parquet(cache_file)
        
        # 2. If cache miss, try loading from source CSV
        if df is None and os.path.exists(source_file):
            try:
                df = pd.read_csv(source_file, index_col='Date', parse_dates=True)
                # Save to cache for next time
                df.to_parquet(cache_file)
            except Exception as e:
                print(f"Error reading source CSV {source_file}: {e}")
                df = None # Reset df if there was an error

        # 3. If still no data, fetch from API
        if df is None:
            print(f"Attempting to fetch data for {symbol} from API...")
            df = self._fetch_data_from_api(symbol, start_date, end_date, timeframe)
            if df is not None:
                # API fetch already saves to CSV, now save to cache
                df.to_parquet(cache_file)

        # 4. Filter by date range
        if df is not None:
            if start_date:
                df = df[df.index >= pd.to_datetime(start_date)]
            if end_date:
                df = df[df.index <= pd.to_datetime(end_date)]

        return df
