import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score
from typing import Tuple, List, Optional

def create_lagged_features(df: pd.DataFrame, lags: List[int], target_column: str = 'Close') -> pd.DataFrame:
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
        df_features[f'{target_column}_lag_{lag}'] = df[target_column].shift(lag)
    return df_features.dropna()

def create_target_binary(df: pd.DataFrame, column: str = 'Close', periods: int = 1) -> pd.Series:
    """
    Creates a binary target variable (1 if price goes up, 0 if down/same).

    Args:
        df (pd.DataFrame): The input DataFrame.
        column (str): The column to base the target on.
        periods (int): The number of periods ahead to look for price change.

    Returns:
        pd.Series: A Series with binary target values.
    """
    # Calculate future price and drop NaN from it directly
    future_price = df[column].shift(-periods).dropna()
    
    # Align the current price with the (now shorter) future_price index
    current_price = df[column].loc[future_price.index]
    
    # Create a boolean series
    target_bool = (future_price > current_price)
    
    return target_bool.astype(int)

def train_model(
    X: pd.DataFrame,
    y: pd.Series,
    model=RandomForestClassifier(n_estimators=100, random_state=42)
) -> Tuple[any, float]:
    """
    Trains a machine learning model and returns the trained model and its accuracy.

    Args:
        X (pd.DataFrame): Feature DataFrame.
        y (pd.Series): Target Series.
        model: The machine learning model to train. Defaults to RandomForestClassifier.

    Returns:
        Tuple[any, float]: A tuple containing the trained model and its accuracy on the test set.
    """
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, shuffle=False, random_state=42)
    model.fit(X_train, y_train)
    y_pred = model.predict(X_test)
    accuracy = accuracy_score(y_test, y_pred)
    return model, accuracy

def predict_with_model(model: any, X_new: pd.DataFrame) -> pd.Series:
    """
    Makes predictions using a trained model.

    Args:
        model (any): The trained machine learning model.
        X_new (pd.DataFrame): New features for prediction.

    Returns:
        pd.Series: A Series of predictions.
    """
    return pd.Series(model.predict(X_new), index=X_new.index)
