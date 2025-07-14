import pytest
import os
import sys
import pandas as pd
import json
import shutil


sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from event_bus import EventBus
from events import MarketEvent, OrderEvent, FillEvent
from data_handler import CSVDataHandler
from execution_handler import SimulatedExecutionHandler
from portfolio import Portfolio
from performance_analyzer import PerformanceAnalyzer
from backtest_manager import BacktestManager

@pytest.fixture
def setup_csv_data(tmp_path):
    # Create a temporary directory for CSV files
    csv_dir = tmp_path / "data"
    csv_dir.mkdir()

    # Create a dummy CSV file with more varied data for testing
    aapl_csv_content = """
datetime,open,high,low,close,volume
2023-01-01,100.00,101.00,99.00,100.50,100000
2023-01-02,100.50,102.00,100.00,101.50,120000
2023-01-03,101.50,103.00,101.00,102.50,150000
2023-01-04,102.50,104.00,102.00,103.50,180000
2023-01-05,103.50,105.00,103.00,104.50,200000
2023-01-06,104.50,106.00,104.00,105.50,220000
2023-01-07,105.50,107.00,105.00,106.50,240000
2023-01-08,106.50,108.00,106.00,107.50,260000
2023-01-09,107.50,109.00,107.00,108.50,280000
2023-01-10,108.50,110.00,108.00,109.50,300000
"""
    (csv_dir / "AAPL.csv").write_text(aapl_csv_content)

    return csv_dir

@pytest.fixture
def setup_portfolio_for_analysis(setup_csv_data):
    csv_dir = setup_csv_data
    events = EventBus()
    data_handler = CSVDataHandler(events, str(csv_dir), ["AAPL"])
    portfolio = Portfolio(data_handler, events, pd.Timestamp('2023-01-01'), 100000.0)
    execution_handler = SimulatedExecutionHandler(events, data_handler)

    # Simulate some trades for testing performance analysis
    # Day 1: Buy 100 shares
    data_handler.update_bars()
    market_event = events.get()
    portfolio.update_timeindex(market_event)
    order1 = OrderEvent("AAPL", "MKT", 100, "BUY")
    execution_handler.execute_order(order1)
    execution_handler.update(market_event) # Fill order
    fill1 = events.get()
    portfolio.update_fill(fill1)

    # Day 2: Price goes up, no trade
    data_handler.update_bars()
    market_event = events.get()
    portfolio.update_timeindex(market_event)
    execution_handler.update(market_event)

    # Day 3: Sell 50 shares (partial close)
    data_handler.update_bars()
    market_event = events.get()
    portfolio.update_timeindex(market_event)
    order2 = OrderEvent("AAPL", "MKT", 50, "SELL")
    execution_handler.execute_order(order2)
    execution_handler.update(market_event) # Fill order
    fill2 = events.get()
    portfolio.update_fill(fill2)

    # Day 4: Price goes down, no trade
    data_handler.update_bars()
    market_event = events.get()
    portfolio.update_timeindex(market_event)
    execution_handler.update(market_event)

    # Day 5: Sell remaining 50 shares (full close)
    data_handler.update_bars()
    market_event = events.get()
    portfolio.update_timeindex(market_event)
    order3 = OrderEvent("AAPL", "MKT", 50, "SELL")
    execution_handler.execute_order(order3)
    execution_handler.update(market_event) # Fill order
    fill3 = events.get()
    portfolio.update_fill(fill3)

    # Ensure equity curve is created
    portfolio.create_equity_curve_dataframe()

    return portfolio, data_handler

# --- PerformanceAnalyzer Tests ---

def test_performance_analyzer_metrics_calculation(setup_portfolio_for_analysis):
    portfolio, data_handler = setup_portfolio_for_analysis
    analyzer = PerformanceAnalyzer(portfolio, data_handler)
    metrics = analyzer.calculate_metrics()

    assert "Total Return (%)" in metrics
    assert "Annualized Return (%)" in metrics
    assert "Max Drawdown (%)" in metrics
    assert "Total Trades" in metrics
    assert metrics["Total Trades"] == 2 # One buy, two sells closing the same position
    assert "Winning Trades" in metrics
    assert "Losing Trades" in metrics
    assert "Profit Factor" in metrics
    assert "Average Profit per Trade" in metrics
    assert "Average Losing Trade Duration (Days)" in metrics

    # Basic check for expected values (adjust based on your dummy data and logic)
    assert metrics["Total Trades"] == len(portfolio.closed_trades)
    assert metrics["Total Trades"] > 0


def test_performance_analyzer_matplotlib_plots(setup_portfolio_for_analysis, tmp_path):
    portfolio, data_handler = setup_portfolio_for_analysis
    analyzer = PerformanceAnalyzer(portfolio, data_handler)

    equity_path = tmp_path / "equity_curve.png"
    drawdown_path = tmp_path / "drawdown.png"

    analyzer.generate_equity_curve_matplotlib(str(equity_path))
    analyzer.generate_drawdown_matplotlib(str(drawdown_path))

    assert equity_path.exists()
    assert drawdown_path.exists()

def test_performance_analyzer_plotly_plots(setup_portfolio_for_analysis, tmp_path):
    portfolio, data_handler = setup_portfolio_for_analysis
    analyzer = PerformanceAnalyzer(portfolio, data_handler)

    equity_html_path = tmp_path / "equity_curve.html"
    drawdown_html_path = tmp_path / "drawdown.html"
    trades_html_path = tmp_path / "trades.html"

    analyzer.generate_equity_curve_plotly(str(equity_html_path))
    analyzer.generate_drawdown_plotly(str(drawdown_html_path))
    analyzer.generate_trades_plotly(str(trades_html_path))

    assert equity_html_path.exists()
    assert drawdown_html_path.exists()
    assert trades_html_path.exists()

# --- BacktestManager Tests ---

def test_backtest_manager_save_and_load(setup_portfolio_for_analysis, tmp_path):
    portfolio, data_handler = setup_portfolio_for_analysis
    analyzer = PerformanceAnalyzer(portfolio, data_handler)
    metrics = analyzer.calculate_metrics()

    backtest_name = "test_backtest_save_load"
    backtest_params = {"test_param": "value"}
    plot_filepaths = {
        "equity_curve_matplotlib": str(tmp_path / "equity_curve.png"),
        "drawdown_matplotlib": str(tmp_path / "drawdown.png"),
        "equity_curve_plotly": str(tmp_path / "equity_curve.html"),
        "drawdown_plotly": str(tmp_path / "drawdown.html"),
        "trades_plotly": str(tmp_path / "trades.html")
    }

    # Generate plots first so they exist for saving
    analyzer.generate_equity_curve_matplotlib(plot_filepaths["equity_curve_matplotlib"])
    analyzer.generate_drawdown_matplotlib(plot_filepaths["drawdown_matplotlib"])
    analyzer.generate_equity_curve_plotly(plot_filepaths["equity_curve_plotly"])
    analyzer.generate_drawdown_plotly(plot_filepaths["drawdown_plotly"])
    analyzer.generate_trades_plotly(plot_filepaths["trades_plotly"])

    manager = BacktestManager(base_dir=str(tmp_path / "backtest_results"))
    manager.save_backtest(backtest_name, portfolio, backtest_params, metrics, plot_filepaths)

    # Verify saved files exist
    saved_path = tmp_path / "backtest_results" / backtest_name
    assert saved_path.exists()
    assert (saved_path / "equity_curve.csv").exists()
    assert (saved_path / "all_positions.csv").exists()
    assert (saved_path / "all_holdings.csv").exists()
    assert (saved_path / "closed_trades.csv").exists()
    assert (saved_path / "backtest_params.json").exists()
    assert (saved_path / "performance_metrics.json").exists()
    assert (saved_path / "equity_curve.png").exists()
    assert (saved_path / "drawdown.png").exists()
    assert (saved_path / "equity_curve.html").exists()
    assert (saved_path / "drawdown.html").exists()
    assert (saved_path / "trades.html").exists()

    # Load and verify content
    loaded_data = manager.load_backtest(backtest_name)
    assert loaded_data is not None
    assert loaded_data["backtest_params"] == backtest_params
    # Compare performance metrics, handling NaN values
    for key, value in metrics.items():
        if isinstance(value, float) and pd.isna(value):
            assert isinstance(loaded_data["performance_metrics"].get(key), float) and pd.isna(loaded_data["performance_metrics"].get(key))
        else:
            assert loaded_data["performance_metrics"].get(key) == value

    # Compare DataFrames (using .equals for content comparison)
    pd.testing.assert_frame_equal(loaded_data["equity_curve"], portfolio.equity_curve)
    pd.testing.assert_frame_equal(loaded_data["all_positions"], pd.DataFrame(portfolio.all_positions))
    pd.testing.assert_frame_equal(loaded_data["all_holdings"], pd.DataFrame(portfolio.all_holdings))
    pd.testing.assert_frame_equal(loaded_data["closed_trades"], pd.DataFrame(portfolio.closed_trades))

    # Clean up the created directory
    shutil.rmtree(manager.base_dir)

# --- Integration Test (Full Backtest Simulation) ---

from backtester import Backtester
from strategy import BuyAndHoldStrategy # Assuming this strategy is simple enough for a quick test

def test_full_backtest_with_reporting(tmp_path):
    # Setup temporary directories for data and results
    csv_dir = tmp_path / "data"
    csv_dir.mkdir()
    results_dir = tmp_path / "backtest_results_integration"

    aapl_csv_content = """
datetime,open,high,low,close,volume
2023-01-01,100.00,101.00,99.00,100.50,100000
2023-01-02,100.50,102.00,100.00,101.50,120000
2023-01-03,101.50,103.00,101.00,102.50,150000
2023-01-04,102.50,104.00,102.00,103.50,180000
2023-01-05,103.50,105.00,103.00,104.50,200000
2023-01-06,104.50,106.00,104.00,105.50,220000
2023-01-07,105.50,107.00,105.00,106.50,240000
2023-01-08,106.50,108.00,106.00,107.50,260000
2023-01-09,107.50,109.00,107.00,108.50,280000
2023-01-10,108.50,110.00,108.00,109.50,300000
"""
    (csv_dir / "AAPL.csv").write_text(aapl_csv_content)

    # Temporarily change the working directory for BacktestManager to save results
    original_cwd = os.getcwd()
    os.chdir(str(tmp_path))

    try:
        # Initialize and run the backtester
        bt = Backtester(
            csv_dir=str(csv_dir),
            symbol_list=["AAPL"],
            initial_capital=100000.0,
            start_date=pd.Timestamp('2023-01-01'),
            heartbeat=0.0,
            data_handler=CSVDataHandler,
            execution_handler=SimulatedExecutionHandler,
            portfolio=Portfolio,
            strategy=BuyAndHoldStrategy
        )
        bt.simulate_trading()

        # Verify that a results directory was created
        # The name will be dynamic, so we check for any directory starting with "backtest_"
        # The BacktestManager saves to a 'backtest_results' directory within the current working directory
        backtest_base_dir = tmp_path / "backtest_results"
        created_dirs = [d for d in os.listdir(backtest_base_dir) if d.startswith("backtest_")]
        assert len(created_dirs) == 1
        backtest_run_dir = backtest_base_dir / created_dirs[0]
        assert backtest_run_dir.is_dir()

        # Verify key files exist within the results directory
        assert (backtest_run_dir / "equity_curve.csv").exists()
        assert (backtest_run_dir / "performance_metrics.json").exists()
        assert (backtest_run_dir / "equity_curve.png").exists()
        assert (backtest_run_dir / "equity_curve.html").exists()
        assert (backtest_run_dir / "trades.html").exists()

        # Load and do a basic check on metrics
        with open(backtest_run_dir / "performance_metrics.json", "r") as f:
            metrics = json.load(f)
        assert "Total Trades" in metrics
        assert metrics["Total Trades"] > 0 # BuyAndHold should make at least one trade

    finally:
        # Restore original working directory
        os.chdir(original_cwd)
        # Clean up the created results directory
        if results_dir.exists():
            shutil.rmtree(results_dir)
