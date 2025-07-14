import os
import json
import pandas as pd

class BacktestManager:
    """
    Manages saving and loading of backtest results.
    """
    def __init__(self, base_dir="backtest_results"):
        self.base_dir = base_dir
        os.makedirs(self.base_dir, exist_ok=True)

    def _get_backtest_path(self, backtest_name):
        return os.path.join(self.base_dir, backtest_name)

    def save_backtest(
        self,
        backtest_name,
        portfolio_obj,
        backtest_params,
        performance_metrics,
        plot_filepaths
    ):
        """
        Saves all relevant backtest data and results.
        """
        backtest_path = self._get_backtest_path(backtest_name)
        os.makedirs(backtest_path, exist_ok=True)

        # Save portfolio data
        if not portfolio_obj.equity_curve.empty:
            portfolio_obj.equity_curve.to_csv(os.path.join(backtest_path, "equity_curve.csv"))
        
        # Convert list of dicts to DataFrame for easier saving
        if portfolio_obj.all_positions:
            pd.DataFrame(portfolio_obj.all_positions).to_csv(os.path.join(backtest_path, "all_positions.csv"), index=False)
        if portfolio_obj.all_holdings:
            pd.DataFrame(portfolio_obj.all_holdings).to_csv(os.path.join(backtest_path, "all_holdings.csv"), index=False)
        if portfolio_obj.closed_trades:
            pd.DataFrame(portfolio_obj.closed_trades).to_csv(os.path.join(backtest_path, "closed_trades.csv"), index=False)

        # Save backtest parameters
        with open(os.path.join(backtest_path, "backtest_params.json"), "w") as f:
            json.dump(backtest_params, f, indent=4)

        # Save performance metrics
        with open(os.path.join(backtest_path, "performance_metrics.json"), "w") as f:
            json.dump(performance_metrics, f, indent=4)

        # Copy plots to the backtest directory
        for plot_type, filepath in plot_filepaths.items():
            if os.path.exists(filepath):
                os.rename(filepath, os.path.join(backtest_path, os.path.basename(filepath)))

        print(f"Backtest results saved to: {backtest_path}")

    def load_backtest(self, backtest_name):
        """
        Loads backtest data and results.
        """
        backtest_path = self._get_backtest_path(backtest_name)
        if not os.path.exists(backtest_path):
            print(f"Backtest '{backtest_name}' not found at {backtest_path}")
            return None

        loaded_data = {}

        # Load portfolio data
        equity_curve_path = os.path.join(backtest_path, "equity_curve.csv")
        if os.path.exists(equity_curve_path):
            loaded_data["equity_curve"] = pd.read_csv(equity_curve_path, index_col=0, parse_dates=True)
        
        all_positions_path = os.path.join(backtest_path, "all_positions.csv")
        if os.path.exists(all_positions_path):
            loaded_data["all_positions"] = pd.read_csv(all_positions_path, parse_dates=['datetime'])
        
        all_holdings_path = os.path.join(backtest_path, "all_holdings.csv")
        if os.path.exists(all_holdings_path):
            loaded_data["all_holdings"] = pd.read_csv(all_holdings_path, parse_dates=['datetime'])

        closed_trades_path = os.path.join(backtest_path, "closed_trades.csv")
        if os.path.exists(closed_trades_path):
            loaded_data["closed_trades"] = pd.read_csv(closed_trades_path, parse_dates=['entry_time', 'exit_time'])

        # Load backtest parameters
        params_path = os.path.join(backtest_path, "backtest_params.json")
        if os.path.exists(params_path):
            with open(params_path, "r") as f:
                loaded_data["backtest_params"] = json.load(f)

        # Load performance metrics
        metrics_path = os.path.join(backtest_path, "performance_metrics.json")
        if os.path.exists(metrics_path):
            with open(metrics_path, "r") as f:
                loaded_data["performance_metrics"] = json.load(f)

        # List plot files (not loading content, just paths)
        loaded_data["plot_files"] = {
            f.split(".")[0]: os.path.join(backtest_path, f)
            for f in os.listdir(backtest_path)
            if f.endswith((".png", ".jpg", ".html"))
        }

        print(f"Backtest results loaded from: {backtest_path}")
        return loaded_data