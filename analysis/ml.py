import pandas as pd
from sklearn.model_selection import train_test_split, TimeSeriesSplit
from sklearn.ensemble import RandomForestClassifier, GradientBoostingRegressor
from sklearn.linear_model import LinearRegression
from sklearn.metrics import (
    accuracy_score,
    mean_absolute_error,
    r2_score,
    mean_squared_error,
)
from typing import Tuple, List, Optional, Dict, Any
import numpy as np


def create_lagged_features(
    df: pd.DataFrame, lags: List[int], target_column: str = "Close"
) -> pd.DataFrame:
    """
    Creates lagged features for a given DataFrame.

    Args:
        df (pd.DataFrame): The input DataFrame.
        lags (List[int]): A list of integers representing the number of periods to lag.
        target_column (str): The column to create lagged features from.

    Returns:
        pd.DataFrame: A new DataFrame with lagged features.
    """
    df_features = pd.DataFrame(index=df.index)
    for lag in lags:
        df_features[f"{target_column}_lag_{lag}"] = df[target_column].shift(lag)
    return df_features.dropna()


def create_target_binary(
    df: pd.DataFrame, column: str = "Close", periods: int = 1
) -> pd.Series:
    """
    Creates a binary target variable (1 if price goes up, 0 if down/same).

    Args:
        df (pd.DataFrame): The input DataFrame.
        column (str): The column to base the target on.
        periods (int): The number of periods ahead to look for price change.

    Returns:
        pd.Series: A Series with binary target values.
    """
    future_price = df[column].shift(-periods).dropna()
    current_price = df[column].loc[future_price.index]
    target_bool = future_price > current_price
    return target_bool.astype(int)


def create_target_regression(
    df: pd.DataFrame, column: str = "Close", periods: int = 1
) -> pd.Series:
    """
    Creates a regression target variable (e.g., next day's price).

    Args:
        df (pd.DataFrame): The input DataFrame.
        column (str): The column to base the target on.
        periods (int): The number of periods ahead to predict.

    Returns:
        pd.Series: A Series with regression target values.
    """
    return df[column].shift(-periods).dropna()


def train_model(
    X: pd.DataFrame,
    y: pd.Series,
    model: Any = RandomForestClassifier(n_estimators=100, random_state=42),
    is_regression: bool = False,
) -> Tuple[Any, Dict[str, float]]:
    """
    Trains a machine learning model and returns the trained model and its evaluation metrics.

    Args:
        X (pd.DataFrame): Feature DataFrame.
        y (pd.Series): Target Series.
        model (Any): The machine learning model to train. Defaults to RandomForestClassifier.
        is_regression (bool): True if it's a regression task, False for classification.

    Returns:
        Tuple[Any, Dict[str, float]]: A tuple containing the trained model and a dictionary of metrics.
    """
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, shuffle=False, random_state=42
    )
    model.fit(X_train, y_train)
    y_pred = model.predict(X_test)

    metrics = {}
    if is_regression:
        metrics = evaluate_regression_model(y_test, y_pred)
    else:
        metrics["accuracy"] = accuracy_score(y_test, y_pred)

    return model, metrics


def evaluate_regression_model(
    y_true: pd.Series, y_pred: np.ndarray
) -> Dict[str, float]:
    """
    Evaluates a regression model and returns common metrics.

    Args:
        y_true (pd.Series): True target values.
        y_pred (np.ndarray): Predicted target values.

    Returns:
        Dict[str, float]: A dictionary of regression metrics.
    """
    return {
        "mae": mean_absolute_error(y_true, y_pred),
        "mse": mean_squared_error(y_true, y_pred),
        "rmse": np.sqrt(mean_squared_error(y_true, y_pred)),
        "r2": r2_score(y_true, y_pred),
    }


def train_model_with_cv(
    X: pd.DataFrame,
    y: pd.Series,
    model: Any,
    n_splits: int = 5,
    is_regression: bool = False,
) -> Tuple[Any, Dict[str, List[float]]]:
    """
    Trains and evaluates a model using time-series cross-validation.

    Args:
        X (pd.DataFrame): Feature DataFrame.
        y (pd.Series): Target Series.
        model (Any): The machine learning model to train.
        n_splits (int): Number of splits for TimeSeriesSplit.
        is_regression (bool): True if it's a regression task, False for classification.

    Returns:
        Tuple[Any, Dict[str, List[float]]]: A tuple containing the last trained model and a dictionary of metrics per fold.
    """
    tscv = TimeSeriesSplit(n_splits=n_splits)
    fold_metrics = {
        metric: []
        for metric in (
            ["accuracy"] if not is_regression else ["mae", "mse", "rmse", "r2"]
        )
    }
    last_model = None

    for train_index, test_index in tscv.split(X):
        X_train, X_test = X.iloc[train_index], X.iloc[test_index]
        y_train, y_test = y.iloc[train_index], y.iloc[test_index]

        model.fit(X_train, y_train)
        y_pred = model.predict(X_test)

        if is_regression:
            metrics = evaluate_regression_model(y_test, y_pred)
            for metric_name, value in metrics.items():
                fold_metrics[metric_name].append(value)
        else:
            fold_metrics["accuracy"].append(accuracy_score(y_test, y_pred))

        last_model = model  # Keep the last trained model

    return last_model, fold_metrics


def predict_with_model(model: Any, X_new: pd.DataFrame) -> pd.Series:
    """
    Makes predictions using a trained model.

    Args:
        model (Any): The trained machine learning model.
        X_new (pd.DataFrame): New features for prediction.

    Returns:
        pd.Series: A Series of predictions.
    """
    return pd.Series(model.predict(X_new), index=X_new.index)


def predict_baseline_mid_price(
    df: pd.DataFrame, column: str = "mid_price", periods: int = 1
) -> pd.Series:
    """
    Predicts the next day's mid-price as simply today's mid-price (a naive baseline).

    Args:
        df (pd.DataFrame): The input DataFrame with the mid-price column.
        column (str): The column containing the mid-price.
        periods (int): The number of periods ahead to predict (should be 1 for next day).

    Returns:
        pd.Series: A Series of baseline predictions.
    """
    # Get the index of the actual target values
    actual_target_index = df[column].shift(-periods).dropna().index

    # The baseline prediction for each date in actual_target_index is the mid_price of that same date
    return df[column].loc[actual_target_index]
