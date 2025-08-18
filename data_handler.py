import pandas as pd
import logging
from events import MarketEvent

logger = logging.getLogger(__name__)

class DataHandler:
    """
    DataHandler is an abstract base class providing an interface for
    all subsequent (inherited) data handlers (both live and historic).
    """
    def get_bars(self, symbol, N=None, start_date=None, end_date=None):
        raise NotImplementedError("Should implement get_bars()")

    def get_latest_bars(self, symbol, N=1):
        """
        Returns the last N bars from the data up to the current time.
        This is a convenience wrapper around get_bars.
        """
        return self.get_bars(symbol, N=N)

    def update_bars(self):
        raise NotImplementedError("Should implement update_bars()")

    

class CSVDataHandler(DataHandler):
    """
    CSVDataHandler is designed to read CSV files for each symbol
    and provide an interface to obtain the latest bar of
    each symbol as well as updating the bars.
    """
    def __init__(self, events, csv_dir, symbol_list):
        self.events = events
        self.csv_dir = csv_dir
        self.symbol_list = symbol_list

        self.symbol_data = {} # Stores the full DataFrame for each symbol
        self.latest_symbol_data = {}
        self.bar_generators = {} # Stores iterators for each symbol
        self.continue_backtest = True
        self.current_time = None
        self._open_convert_csv_files()

    def _open_convert_csv_files(self):
        """
        Opens the CSV files from the data directory, converting
        them into pandas DataFrames within a symbol dictionary.
        For this handler, all CSV files are assumed to have
        the columns of 'datetime', 'open', 'high', 'low', 'close', 'volume'.
        """
        logger.info("Loading and preparing historical data...")
        comb_index = None
        for s in self.symbol_list:
            # Load the CSV file with no header information,
            # indexed on datetime
            file_path = f"{self.csv_dir}/{s}.csv"
            try:
                self.symbol_data[s] = pd.read_csv(
                    file_path, header=0, index_col=0, parse_dates=True, nrows=1000
                )
                self.symbol_data[s].columns = [col.lower() for col in self.symbol_data[s].columns]
                logger.debug(f"Successfully loaded {file_path} for symbol {s}")
            except FileNotFoundError:
                logger.error(f"CSV file not found for symbol {s} at {file_path}")
                # Decide how to handle this - e.g., skip the symbol or raise an exception
                continue # Skip this symbol

            if comb_index is None:
                comb_index = self.symbol_data[s].index
            else:
                comb_index = comb_index.union(self.symbol_data[s].index)

        # Reindex the dataframes
        for s in self.symbol_list:
            if s in self.symbol_data:
                self.symbol_data[s] = self.symbol_data[s].reindex(
                    index=comb_index, method='pad'
                )
        self.bar_generators = {s: self.symbol_data[s].iterrows() for s in self.symbol_list if s in self.symbol_data}
        logger.info("Historical data loaded and prepared.")

    def _get_new_bar(self, symbol):
        """
        Returns the iterator for the next bar from the data feed.
        """
        return self.bar_generators[symbol]

    def get_bars(self, symbol, N=None, start_date=None, end_date=None):
        """
        Returns historical bars for a given symbol.

        - If N is provided, returns the last N bars up to the current backtest time.
        - If start_date and/or end_date are provided, returns bars within that date range.
        - If no parameters are provided, returns all historical bars up to the current time.
        """
        if symbol not in self.symbol_data:
            logger.error(f"Symbol {symbol} not found in historical data set.")
            return pd.DataFrame()

        if self.current_time is None:
            logger.warning("Backtest has not started, no historical data to return.")
            return pd.DataFrame()

        # Filter data up to the current backtest time
        data = self.symbol_data[symbol].loc[:self.current_time]

        # Filter by date range
        if start_date:
            data = data.loc[start_date:]
        if end_date:
            data = data.loc[:end_date]

        # Return last N bars if specified
        if N is not None:
            return data.tail(N)
        
        return data

    def get_latest_bars(self, symbol, N=1):
        """
        Returns the last N bars from the data up to the current time.
        This is a convenience wrapper around get_bars.
        """
        return self.get_bars(symbol, N=N)

    def update_bars(self):
        """
        Pushes the latest bar to the latest_symbol_data structure
        and adds a MarketEvent to the events queue.
        """
        for s in self.symbol_list:
            try:
                bar = next(self._get_new_bar(s))
            except StopIteration:
                self.continue_backtest = False
            else:
                if s not in self.latest_symbol_data:
                    self.latest_symbol_data[s] = []
                self.latest_symbol_data[s].append(bar)
        if self.continue_backtest:
            # Get the current datetime from the latest bar of the first symbol
            self.current_time = self.latest_symbol_data[self.symbol_list[0]][-1][0]
            self.events.put(MarketEvent(self.current_time))
