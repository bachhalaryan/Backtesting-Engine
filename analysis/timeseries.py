import pandas as pd
import ta


def calculate_sma(df: pd.DataFrame, window: int, column: str = "Close") -> pd.Series:
    """
    Calculates the Simple Moving Average (SMA) for a given DataFrame and window.

    Args:
        df (pd.DataFrame): The input DataFrame with a 'Close' column.
        window (int): The lookback window for the SMA.
        column (str): The column to calculate SMA on. Defaults to 'Close'.

    Returns:
        pd.Series: A Series containing the SMA values.
    """
    return ta.trend.sma_indicator(df[column], window, fillna=False)


def calculate_ema(df: pd.DataFrame, window: int, column: str = "Close") -> pd.Series:
    """
    Calculates the Exponential Moving Average (EMA) for a given DataFrame and window.

    Args:
        df (pd.DataFrame): The input DataFrame with a 'Close' column.
        window (int): The lookback window for the EMA.
        column (str): The column to calculate EMA on. Defaults to 'Close'.

    Returns:
        pd.Series: A Series containing the EMA values.
    """
    return ta.trend.ema_indicator(df[column], window, fillna=False)


def calculate_rsi(df: pd.DataFrame, window: int, column: str = "Close") -> pd.Series:
    """
    Calculates the Relative Strength Index (RSI) for a given DataFrame and window.

    Args:
        df (pd.DataFrame): The input DataFrame with a 'Close' column.
        window (int): The lookback window for the RSI.
        column (str): The column to calculate RSI on. Defaults to 'Close'.

    Returns:
        pd.Series: A Series containing the RSI values.
    """
    df_lower = df.rename(columns=str.lower)
    return ta.momentum.rsi(df_lower[column.lower()], window, fillna=False)


def calculate_bollinger_bands(
    df: pd.DataFrame, window: int, window_dev: float, column: str = "Close"
) -> pd.DataFrame:
    """
    Calculates Bollinger Bands (BB) for a given DataFrame.

    Args:
        df (pd.DataFrame): The input DataFrame with a 'Close' column.
        window (int): The lookback window for the Bollinger Bands.
        window_dev (float): The number of standard deviations for the bands.
        column (str): The column to calculate BB on. Defaults to 'Close'.

    Returns:
        pd.DataFrame: A DataFrame with 'bb_bbm', 'bb_bbh', 'bb_bbl' columns.
    """
    bollinger = ta.volatility.BollingerBands(
        close=df[column], window=window, window_dev=window_dev, fillna=False
    )
    return pd.DataFrame(
        {
            "bb_bbm": bollinger.bollinger_mavg(),
            "bb_bbh": bollinger.bollinger_hband(),
            "bb_bbl": bollinger.bollinger_lband(),
        }
    )


def calculate_mid_price(df: pd.DataFrame) -> pd.Series:
    """
    Calculates the mid-price ( (High + Low) / 2 ) for a given DataFrame.

    Args:
        df (pd.DataFrame): The input DataFrame with 'High' and 'Low' columns.

    Returns:
        pd.Series: A Series containing the mid-price values.
    """
    if "High" not in df.columns or "Low" not in df.columns:
        raise ValueError(
            "DataFrame must contain 'High' and 'Low' columns to calculate mid-price."
        )
    return (df["High"] + df["Low"]) / 2
