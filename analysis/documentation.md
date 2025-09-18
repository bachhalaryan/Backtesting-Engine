# Analysis Module Documentation

This document provides an overview and usage instructions for the `analysis` module, which contains tools for data management, time series analysis, and machine learning for financial data.

## 1. DataManager

The `DataManager` class is responsible for loading, caching, and fetching financial time series data from various sources.

### `DataManager(data_path='./data', cache_path='./cache')`

Initializes the DataManager.

-   `data_path` (str): The directory where local CSV data files are stored. The DataManager will look for files in the format `{symbol}_{timeframe}.csv`.
-   `cache_path` (str): The directory where processed data will be cached in Parquet format for faster subsequent access. Cache files are named `{symbol}_{timeframe}.parquet`.

### `get_data(symbol: str, start_date: Optional[str] = None, end_date: Optional[str] = None, timeframe: str = '1d') -> Optional[pd.DataFrame]`

Loads historical data for a given symbol and timeframe. The method prioritizes data sources in the following order:

1.  **Cache:** Checks `cache_path` for a Parquet file.
2.  **Local CSV:** Checks `data_path` for a CSV file.
3.  **API (yfinance):** If not found locally, attempts to fetch data from Yahoo Finance. API-fetched data is then saved to both the local CSV and the cache for future use.

**Parameters:**

-   `symbol` (str): The ticker symbol (e.g., 'AAPL', 'EURUSD').
-   `start_date` (Optional[str]): The start date for the data in 'YYYY-MM-DD' format. If `None`, fetches all available data.
-   `end_date` (Optional[str]): The end date for the data in 'YYYY-MM-DD' format. If `None`, fetches data up to the most recent available.
-   `timeframe` (str): The data aggregation period (e.g., '1d' for daily). Currently, API fetching primarily supports '1d'.

**Returns:**

-   `pd.DataFrame`: A DataFrame containing the historical data, indexed by 'Date', with columns like 'Open', 'High', 'Low', 'Close', 'Volume'. Returns `None` if data cannot be retrieved.

**Usage Example:**

```python
from analysis.data_manager import DataManager

dm = DataManager(data_path='./my_data', cache_path='./my_cache')

# Get daily data for AAPL, fetching from API if not available locally/cached
aapl_df = dm.get_data(symbol='AAPL', start_date='2020-01-01', end_date='2023-12-31', timeframe='1d')

if aapl_df is not None:
    print(aapl_df.head())

# Get data for a symbol that might only be in your local CSV
eurusd_df = dm.get_data(symbol='EURUSD', start_date='2022-01-01')
```

## 2. Time Series Analysis (`timeseries.py`)

This module provides functions to calculate common technical indicators.

### `calculate_sma(df: pd.DataFrame, window: int, column: str = 'Close') -> pd.Series`

Calculates the Simple Moving Average (SMA).

-   `df` (pd.DataFrame): Input DataFrame with a 'Close' column (or specified `column`).
-   `window` (int): The lookback period for the SMA.
-   `column` (str): The column to calculate SMA on. Defaults to 'Close'.

**Returns:** `pd.Series` with SMA values.

### `calculate_ema(df: pd.DataFrame, window: int, column: str = 'Close') -> pd.Series`

Calculates the Exponential Moving Average (EMA).

-   `df` (pd.DataFrame): Input DataFrame.
-   `window` (int): The lookback period for the EMA.
-   `column` (str): The column to calculate EMA on. Defaults to 'Close'.

**Returns:** `pd.Series` with EMA values.

### `calculate_rsi(df: pd.DataFrame, window: int, column: str = 'Close') -> pd.Series`

Calculates the Relative Strength Index (RSI).

-   `df` (pd.DataFrame): Input DataFrame.
-   `window` (int): The lookback period for the RSI.
-   `column` (str): The column to calculate RSI on. Defaults to 'Close'.

**Returns:** `pd.Series` with RSI values.

### `calculate_bollinger_bands(df: pd.DataFrame, window: int, window_dev: float, column: str = 'Close') -> pd.DataFrame`

Calculates Bollinger Bands (BB).

-   `df` (pd.DataFrame): Input DataFrame.
-   `window` (int): The lookback period for the Bollinger Bands.
-   `window_dev` (float): The number of standard deviations for the bands.
-   `column` (str): The column to calculate BB on. Defaults to 'Close'.

**Returns:** `pd.DataFrame` with 'bb_bbm' (middle band), 'bb_bbh' (upper band), 'bb_bbl' (lower band) columns.

**Usage Example:**

```python
from analysis.timeseries import calculate_sma, calculate_rsi
# Assuming aapl_df is loaded from DataManager

aapl_df['SMA_20'] = calculate_sma(aapl_df, window=20)
aapl_df['RSI_14'] = calculate_rsi(aapl_df, window=14)
bb_df = calculate_bollinger_bands(aapl_df, window=20, window_dev=2)
aapl_df = aapl_df.join(bb_df) # Add Bollinger Bands to the main DataFrame

print(aapl_df.tail())
```

## 3. Machine Learning (`ml.py`)

This module provides functions for feature engineering, target variable creation, model training, and prediction.

### `create_lagged_features(df: pd.DataFrame, lags: List[int], target_column: str = 'Close') -> pd.DataFrame`

Creates lagged features from a specified column.

-   `df` (pd.DataFrame): Input DataFrame.
-   `lags` (List[int]): A list of integers representing the number of periods to lag (e.g., `[1, 5]` for 1-period and 5-period lags).
-   `target_column` (str): The column to create lagged features from. Defaults to 'Close'.

**Returns:** `pd.DataFrame` with lagged features, indexed by the original DataFrame's index, with `NaN` rows removed.

### `create_target_binary(df: pd.DataFrame, column: str = 'Close', periods: int = 1) -> pd.Series`

Creates a binary target variable (1 if price goes up, 0 if down/same) based on future price movement.

-   `df` (pd.DataFrame): Input DataFrame.
-   `column` (str): The column to base the target on (e.g., 'Close').
-   `periods` (int): The number of periods ahead to look for price change. A value of `1` means predicting if the next period's price is higher.

**Returns:** `pd.Series` with binary target values (0 or 1), with `NaN` values removed.

### `train_model(X: pd.DataFrame, y: pd.Series, model=RandomForestClassifier(n_estimators=100, random_state=42)) -> Tuple[any, float]`

Trains a machine learning model.

-   `X` (pd.DataFrame): Feature DataFrame.
-   `y` (pd.Series): Target Series.
-   `model`: The machine learning model instance to train. Defaults to `RandomForestClassifier`.

**Returns:** A tuple containing the trained model object and its accuracy on the test set.

### `predict_with_model(model: any, X_new: pd.DataFrame) -> pd.Series`

Makes predictions using a trained model.

-   `model` (any): The trained machine learning model object.
-   `X_new` (pd.DataFrame): New features for which to make predictions.

**Returns:** `pd.Series` of predictions (e.g., 0 or 1 for classification).

**Usage Example:**

```python
from analysis.ml import create_lagged_features, create_target_binary, train_model, predict_with_model
# Assuming aapl_df is loaded and has indicators calculated

# 1. Create Features
features_df = create_lagged_features(aapl_df, lags=[1, 5, 10], target_column='Close')

# 2. Create Target
target_series = create_target_binary(aapl_df, column='Close', periods=1)

# 3. Align Features and Target (important for time series)
common_index = features_df.index.intersection(target_series.index)
X = features_df.loc[common_index]
y = target_series.loc[common_index]

# 4. Train Model
trained_model, accuracy = train_model(X, y)
print(f"Model Accuracy: {accuracy:.2f}")

# 5. Make Predictions
# For new data, you would create features for that data (e.g., the last few rows of aapl_df)
# For demonstration, let's predict on the training data itself
predictions = predict_with_model(trained_model, X)
print(predictions.tail())
```
