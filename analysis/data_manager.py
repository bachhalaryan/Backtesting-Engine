import pandas as pd
from typing import List, Optional, Union

class DataManager:
    """
    Manages loading, processing, and accessing financial data for analysis.
    """

    def __init__(self, data_path: str = './data'):
        """
        Initializes the DataManager.

        Args:
            data_path (str): The base directory where data is stored.
        """
        self.data_path = data_path
        # In the future, we can add connections to databases or APIs here.

    def get_data(
        self,
        symbol: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        timeframe: str = '1d',
    ) -> Optional[pd.DataFrame]:
        """
        Loads data for a given symbol and timeframe.

        For now, assumes data is in CSV files in the format:
        {data_path}/{symbol}_{timeframe}.csv

        Args:
            symbol (str): The ticker symbol to load (e.g., 'AAPL').
            start_date (Optional[str]): The start date in 'YYYY-MM-DD' format.
            end_date (Optional[str]): The end date in 'YYYY-MM-DD' format.
            timeframe (str): The data timeframe (e.g., '1d', '1h', '1m').

        Returns:
            Optional[pd.DataFrame]: A DataFrame with the loaded data, or None if not found.
        """
        file_path = f"{self.data_path}/{symbol.upper()}_{timeframe}.csv"
        try:
            df = pd.read_csv(file_path, index_col='Date', parse_dates=True)
            
            # Filter by date range
            if start_date:
                df = df[df.index >= pd.to_datetime(start_date)]
            if end_date:
                df = df[df.index <= pd.to_datetime(end_date)]

            return df
        except FileNotFoundError:
            print(f"Data file not found: {file_path}")
            return None
