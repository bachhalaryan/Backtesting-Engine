# Vectorized Backtesting Engine

This is a Python-based event-driven backtesting engine for developing and testing quantitative trading strategies. It provides a modular and extensible framework for backtesting various strategies on historical data.

## Features

*   **Event-Driven Architecture:** The engine uses an event-driven architecture to simulate trading, which makes it more realistic and flexible than a simple vectorized backtester.
*   **Modular Design:** The components of the engine, such as the data handler, strategy, portfolio, and execution handler, are modular and can be easily replaced or extended.
*   **Multiple Strategy Support:** The engine supports the development and testing of multiple trading strategies.
*   **Performance Analysis:** The engine provides a comprehensive performance analysis of the backtest, including various metrics and plots.
*   **Data Analysis Module:** The engine includes a data analysis module for fetching, analyzing, and visualizing financial data.

## Project Structure

```
├── analysis/
│   ├── data_manager.py
│   ├── documentation.md
│   ├── ml.py
│   └── timeseries.py
├── backtest_results/
├── data/
├── strategies/
│   ├── bollinger_band_strategy.py
│   └── ema_rsi_strategy.py
├── tests/
├── .gitignore
├── backtest_manager.py
├── backtester.py
├── data_handler.py
├── event_bus.py
├── events.py
├── execution_handler.py
├── logging_config.py
├── main.py
├── performance_analyzer.py
├── portfolio.py
├── README.md
├── requirements.txt
└── strategy.py
```

*   **`analysis/`**: Contains modules for data management, time series analysis, and machine learning.
*   **`backtest_results/`**: Stores the results of each backtest, including performance metrics and plots.
*   **`data/`**: Contains the historical data files in CSV format.
*   **`strategies/`**: Contains the trading strategy implementations.
*   **`tests/`**: Contains the unit tests for the project.
*   **`backtest_manager.py`**: Manages the backtest results.
*   **`backtester.py`**: The main backtesting engine.
*   **`data_handler.py`**: Manages and provides market data to the backtester.
*   **`event_bus.py`**: The event bus for communication between components.
*   **`events.py`**: Defines the different types of events used in the engine.
*   **`execution_handler.py`**: Simulates trade execution.
*   **`logging_config.py`**: Configures the logging for the project.
*   **`main.py`**: The entry point of the application.
*   **`performance_analyzer.py`**: Analyzes the performance of the backtest.
*   **`portfolio.py`**: Manages the trading portfolio.
*   **`README.md`**: This file.
*   **`requirements.txt`**: The list of Python dependencies.
*   **`strategy.py`**: A base class for trading strategies.

## Getting Started

### Prerequisites

*   Python 3.10 or higher
*   pip

### Installation

1.  Clone the repository:

    ```bash
    git clone https://github.com/your-username/your-repository.git
    ```

2.  Install the dependencies:

    ```bash
    pip install -r requirements.txt
    ```

### Usage

1.  Place your historical data files in the `data/` directory. The data should be in CSV format, with the first column being the date and the following columns being the open, high, low, close, and volume.

2.  Configure the backtest in `main.py`. You can set the symbol list, initial capital, start date, and other parameters.

3.  Run the backtest:

    ```bash
    python main.py
    ```

The backtest results will be saved in the `backtest_results/` directory.

## Strategies

To create a new trading strategy, you need to create a new class that inherits from the `Strategy` class in `strategy.py`. The new class should implement the `calculate_signals` method, which generates trading signals based on the market data.

## Analysis Module

The `analysis` module provides tools for data management, time series analysis, and machine learning for financial data. The `DataManager` class can be used to load, cache, and resample financial time series data. The `timeseries.py` module provides functions to calculate common technical indicators, and the `ml.py` module provides functions for feature engineering, model training, and prediction.

## Contributing

Contributions are welcome! Please feel free to submit a pull request or open an issue.
