import pandas as pd
from events import MarketEvent

class DataHandler:
    """
    DataHandler is an abstract base class providing an interface for
    all subsequent (inherited) data handlers (both live and historic).
    """
    def get_latest_bars(self, symbol, N=1):
        raise NotImplementedError("Should implement get_latest_bars()")

    def update_bars(self):
        raise NotImplementedError("Should implement update_bars()")

    def get_historical_bars(self, symbol, N=None):
        raise NotImplementedError("Should implement get_historical_bars()")

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
        self._open_convert_csv_files()

    def _open_convert_csv_files(self):
        """
        Opens the CSV files from the data directory, converting
        them into pandas DataFrames within a symbol dictionary.
        For this handler, all CSV files are assumed to have
        the columns of 'datetime', 'open', 'high', 'low', 'close', 'volume'.
        """
        comb_index = None
        for s in self.symbol_list:
            # Load the CSV file with no header information,
            # indexed on datetime
            file_path = f"{self.csv_dir}/{s}.csv"
            self.symbol_data[s] = pd.read_csv(
                file_path, header=0, index_col=0, parse_dates=True
            )

            if comb_index is None:
                comb_index = self.symbol_data[s].index
            else:
                comb_index = comb_index.union(self.symbol_data[s].index)

        # Reindex the dataframes
        for s in self.symbol_list:
            self.symbol_data[s] = self.symbol_data[s].reindex(
                index=comb_index, method='pad'
            )
        self.bar_generators = {s: self.symbol_data[s].iterrows() for s in self.symbol_list}

    def _get_new_bar(self, symbol):
        """
        Returns the iterator for the next bar from the data feed.
        """
        return self.bar_generators[symbol]

    def get_latest_bars(self, symbol, N=1):
        """
        Returns the last N bars from the latest_symbol_data dictionary.
        """
        try:
            bars_list = self.latest_symbol_data[symbol]
        except KeyError:
            print("This symbol is not available in the historical data set.")
            return [] # Return empty list if symbol not found
        else:
            return bars_list[-N:]

    def get_historical_bars(self, symbol, N=None):
        """
        Returns the last N historical bars for a given symbol from the full dataset.
        If N is None, returns all historical bars.
        """
        if symbol not in self.symbol_data:
            print(f"Symbol {symbol} not found in historical data.")
            return pd.DataFrame()
        
        if N is None:
            return self.symbol_data[symbol]
        else:
            # Ensure we don't try to return more bars than available
            return self.symbol_data[symbol].iloc[-N:]

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
            current_timeindex = self.latest_symbol_data[self.symbol_list[0]][-1][0]
            self.events.put(MarketEvent(current_timeindex))
