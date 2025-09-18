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

### `calculate_mid_price(df: pd.DataFrame) -> pd.Series`

Calculates the mid-price ( (high + low) / 2 ) for a given DataFrame.

-   `df` (pd.DataFrame): The input DataFrame with 'high' and 'low' columns.

**Returns:** `pd.Series` containing the mid-price values.

**Usage Example:**

```python
from analysis.timeseries import calculate_sma, calculate_rsi, calculate_mid_price
# Assuming aapl_df is loaded from DataManager

aapl_df['SMA_20'] = calculate_sma(aapl_df, window=20)
aapl_df['RSI_14'] = calculate_rsi(aapl_df, window=14)
bb_df = calculate_bollinger_bands(aapl_df, window=20, window_dev=2)
aapl_df = aapl_df.join(bb_df) # Add Bollinger Bands to the main DataFrame
aapl_df['mid_price'] = calculate_mid_price(aapl_df)

print(aapl_df.tail())
```

## 3. Machine Learning (`ml.py`)

This module provides functions for feature engineering, target variable creation, model training, and prediction, supporting both classification and regression tasks.

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

### `create_target_regression(df: pd.DataFrame, column: str = 'Close', periods: int = 1) -> pd.Series`

Creates a regression target variable (e.g., next day's price).

-   `df` (pd.DataFrame): The input DataFrame.
-   `column` (str): The column to base the target on.
-   `periods` (int): The number of periods ahead to predict.

**Returns:** `pd.Series` with regression target values.

### `train_model(X: pd.DataFrame, y: pd.Series, model: Any, is_regression: bool = False) -> Tuple[Any, Dict[str, float]]`

Trains a machine learning model and returns the trained model and its evaluation metrics.

-   `X` (pd.DataFrame): Feature DataFrame.
-   `y` (pd.Series): Target Series.
-   `model` (Any): The machine learning model instance to train (e.g., `RandomForestClassifier()`, `LinearRegression()`, `GradientBoostingRegressor()`).
-   `is_regression` (bool): Set to `True` for regression tasks, `False` for classification. Defaults to `False`.

**Returns:** A tuple containing the trained model object and a dictionary of metrics (e.g., `{'accuracy': 0.85}` for classification, or `{'mae': 0.5, 'rmse': 0.7, 'r2': 0.9}` for regression).

### `evaluate_regression_model(y_true: pd.Series, y_pred: np.ndarray) -> Dict[str, float]`

Evaluates a regression model and returns common metrics.

-   `y_true` (pd.Series): True target values.
-   `y_pred` (np.ndarray): Predicted target values.

**Returns:** A dictionary of regression metrics (`'mae'`, `'mse'`, `'rmse'`, `'r2'`).

### `train_model_with_cv(X: pd.DataFrame, y: pd.Series, model: Any, n_splits: int = 5, is_regression: bool = False) -> Tuple[Any, Dict[str, List[float]]]`

Trains and evaluates a model using time-series cross-validation.

-   `X` (pd.DataFrame): Feature DataFrame.
-   `y` (pd.Series): Target Series.
-   `model` (Any): The machine learning model to train.
-   `n_splits` (int): Number of splits for `TimeSeriesSplit`. Defaults to 5.
-   `is_regression` (bool): Set to `True` for regression tasks, `False` for classification. Defaults to `False`.

**Returns:** A tuple containing the last trained model and a dictionary of metrics per fold (e.g., `{'mae': [0.5, 0.6, 0.55]}`).

### `predict_with_model(model: Any, X_new: pd.DataFrame) -> pd.Series`

Makes predictions using a trained model.

-   `model` (Any): The trained machine learning model object.
-   `X_new` (pd.DataFrame): New features for which to make predictions.

**Returns:** `pd.Series` of predictions.

### `predict_baseline_mid_price(df: pd.DataFrame, column: str = 'mid_price', periods: int = 1) -> pd.Series`

Predicts the next day's mid-price as simply today's mid-price (a naive baseline).

-   `df` (pd.DataFrame): The input DataFrame with the mid-price column.
-   `column` (str): The column containing the mid-price. Defaults to 'mid_price'.
-   `periods` (int): The number of periods ahead to predict (should be 1 for next day). Defaults to 1.

**Returns:** `pd.Series` of baseline predictions, aligned with the target's index.

**Usage Example: Gradient Boosting for Next Day Mid-Price Prediction**

```python
import pandas as pd
from analysis.data_manager import DataManager
from analysis.timeseries import calculate_mid_price
from analysis.ml import (
    create_lagged_features, create_target_regression,
    train_model, evaluate_regression_model,
    train_model_with_cv, predict_baseline_mid_price
)
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.model_selection import train_test_split
import numpy as np

# --- 1. Data Acquisition ---
# Ensure you have data for the symbol in your ./data directory or it can be fetched by yfinance
dm = DataManager(data_path='./data', cache_path='./cache')
symbol = 'AAPL' # Or any other symbol you have data for
df = dm.get_data(symbol=symbol, start_date='2010-01-01', end_date='2023-12-31', timeframe='1d')

if df is None or df.empty:
    print(f"Could not retrieve data for {symbol}. Please ensure data is available.")
    # You might want to raise an error or exit here in a real application
    # exit()

# --- 2. Feature Engineering ---
# Calculate mid-price (now expects lowercase 'high' and 'low')
df['mid_price'] = calculate_mid_price(df)

# Define features to use (high, low, mid_price)
feature_columns = ['high', 'low', 'mid_price'] # Use lowercase
lags = [1] # One day past bar

# Create lagged features for high, low, and mid_price
# We need to create lagged features for each column separately and then combine
all_features_df = pd.DataFrame(index=df.index)
for col in feature_columns:
    lagged_col_df = create_lagged_features(df, lags, target_column=col) # target_column is now lowercase
    all_features_df = all_features_df.join(lagged_col_df, how='outer')

# --- 3. Target Variable Creation ---
# Target: Next day's mid-price
target_series = create_target_regression(df, column='mid_price', periods=1) # column is lowercase

# --- 4. Align Features and Target ---
# Drop any rows with NaN values that resulted from lagging or shifting
combined_df = all_features_df.join(target_series.rename('target'), how='inner').dropna()

X = combined_df.drop('target', axis=1)
y = combined_df['target']

# --- 5. Train/Test Split ---
# Use shuffle=False for time series data to preserve temporal order
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, shuffle=False, random_state=42)

# --- 6. Model Training & Evaluation ---

# Define the Gradient Boosting Regressor model
gb_model = GradientBoostingRegressor(n_estimators=100, learning_rate=0.1, max_depth=3, random_state=42)

print("\n--- Training Gradient Boosting Model (Single Split) ---")
trained_gb_model, gb_metrics = train_model(X_train, y_train, model=gb_model, is_regression=True)
print(f"Gradient Boosting Model Metrics (Test Set): {gb_metrics}")

# --- 7. Baseline Model Comparison ---
print("\n--- Baseline Model (Naive Prediction) ---")
# Generate baseline predictions for the entire dataset
full_baseline_predictions = predict_baseline_mid_price(df, column='mid_price', periods=1) # column is lowercase
# Align baseline predictions with the test set's target index
y_baseline_pred = full_baseline_predictions.loc[y_test.index]

baseline_metrics = evaluate_regression_model(y_test, y_baseline_pred)
print(f"Baseline Model Metrics (Test Set): {baseline_metrics}")

# --- 8. Fold Testing (Time-Series Cross-Validation) ---
print("\n--- Time-Series Cross-Validation for Gradient Boosting Model ---")
# Re-initialize model for CV to ensure fresh state for each fold
gb_model_cv = GradientBoostingRegressor(n_estimators=100, learning_rate=0.1, max_depth=3, random_state=42)
final_gb_model_cv, gb_cv_metrics = train_model_with_cv(X, y, model=gb_model_cv, n_splits=5, is_regression=True)

for metric_name, values in gb_cv_metrics.items():
    print(f"  {metric_name.upper()} per fold: {values}")
    print(f"  Average {metric_name.upper()} across folds: {np.mean(values):.4f}")

# --- 9. Making Predictions with the Trained Model ---
# Example: Predict for the last few days in your dataset (if you have future data or want to predict out-of-sample)
# For this example, let's predict on the last few rows of X_test
# last_X_test_rows = X_test.tail(5)
# predictions = predict_with_model(trained_gb_model, last_X_test_rows)
# print("\nExample Predictions:")
# print(predictions)
```
