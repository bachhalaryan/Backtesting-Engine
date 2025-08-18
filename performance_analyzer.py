import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import plotly.graph_objects as go
from datetime import timedelta
import logging

logger = logging.getLogger(__name__)

class PerformanceAnalyzer:
    """
    Analyzes the performance of a backtest, calculates various metrics,
    and generates plots.
    """
    def __init__(self, portfolio, data_handler):
        self.portfolio = portfolio
        self.equity_curve = portfolio.equity_curve
        self.closed_trades = portfolio.closed_trades
        self.data_handler = data_handler # Needed for fetching price data for trade plots

    def calculate_metrics(self):
        """
        Calculates a comprehensive set of performance metrics.
        """
        metrics = {}

        # --- General Portfolio Metrics ---
        if not self.equity_curve.empty:
            total_return = (self.equity_curve["equity_curve"].iloc[-1] / self.equity_curve["equity_curve"].iloc[0]) - 1
            metrics["Total Return (%)"] = total_return * 100

            # Annualized Return
            years = (self.equity_curve.index[-1] - self.equity_curve.index[0]).days / 365.25
            if years > 0:
                metrics["Annualized Return (%)"] = ((1 + total_return)**(1/years) - 1) * 100
            else:
                metrics["Annualized Return (%)"] = 0.0

            # Annualized Volatility
            daily_returns = self.equity_curve["returns"].dropna()
            if not daily_returns.empty:
                metrics["Annualized Volatility (%)"] = daily_returns.std() * np.sqrt(252) * 100
            else:
                metrics["Annualized Volatility (%)"] = 0.0

            # Sharpe Ratio (assuming risk-free rate is 0 for simplicity)
            if metrics["Annualized Volatility (%)"] > 0:
                metrics["Sharpe Ratio"] = metrics["Annualized Return (%)"] / metrics["Annualized Volatility (%)"]
            else:
                metrics["Sharpe Ratio"] = 0.0

            # Max Drawdown
            peak = self.equity_curve["equity_curve"].expanding(min_periods=1).max()
            drawdown = (self.equity_curve["equity_curve"] - peak) / peak
            metrics["Max Drawdown (%)"] = drawdown.min() * 100

            # Max Drawdown Duration
            if not drawdown.empty:
                max_drawdown_end = drawdown.idxmin()
                peak_before_drawdown = peak.loc[:max_drawdown_end].idxmax()
                metrics["Max Drawdown Duration (Days)"] = (max_drawdown_end - peak_before_drawdown).days
            else:
                metrics["Max Drawdown Duration (Days)"] = 0

            # Calmar Ratio
            if metrics["Max Drawdown (%)"] != 0:
                metrics["Calmar Ratio"] = metrics["Annualized Return (%)"] / abs(metrics["Max Drawdown (%)"])
            else:
                metrics["Calmar Ratio"] = 0.0
        else:
            metrics["Total Return (%)"] = 0.0
            metrics["Annualized Return (%)"] = 0.0
            metrics["Annualized Volatility (%)"] = 0.0
            metrics["Sharpe Ratio"] = 0.0
            metrics["Max Drawdown (%)"] = 0.0
            metrics["Max Drawdown Duration (Days)"] = 0
            metrics["Calmar Ratio"] = 0.0

        # --- Trade-Specific Metrics ---
        metrics["Total Trades"] = len(self.closed_trades)
        
        winning_trades = [t for t in self.closed_trades if t['pnl'] > 0]
        losing_trades = [t for t in self.closed_trades if t['pnl'] < 0]
        
        metrics["Winning Trades"] = len(winning_trades)
        metrics["Losing Trades"] = len(losing_trades)
        
        if metrics["Total Trades"] > 0:
            metrics["Winning Percentage (%)"] = (metrics["Winning Trades"] / metrics["Total Trades"]) * 100
        else:
            metrics["Winning Percentage (%)"] = 0.0

        gross_profit = sum(t['pnl'] for t in winning_trades)
        gross_loss = sum(t['pnl'] for t in losing_trades)
        
        metrics["Gross Profit"] = gross_profit
        metrics["Gross Loss"] = gross_loss

        if gross_loss != 0:
            metrics["Profit Factor"] = abs(gross_profit / gross_loss)
        else:
            metrics["Profit Factor"] = np.inf if gross_profit > 0 else 0.0

        if metrics["Winning Trades"] > 0:
            metrics["Average Profit per Trade"] = gross_profit / metrics["Winning Trades"]
        else:
            metrics["Average Profit per Trade"] = 0.0

        if metrics["Losing Trades"] > 0:
            metrics["Average Loss per Trade"] = gross_loss / metrics["Losing Trades"]
        else:
            metrics["Average Loss per Trade"] = 0.0

        if metrics["Average Loss per Trade"] != 0:
            metrics["Ratio Avg Win / Avg Loss"] = abs(metrics["Average Profit per Trade"] / metrics["Average Loss per Trade"])
        else:
            metrics["Ratio Avg Win / Avg Loss"] = np.inf if metrics["Average Profit per Trade"] > 0 else 0.0

        # Max Consecutive Wins/Losses
        max_consecutive_wins = 0
        current_consecutive_wins = 0
        max_consecutive_losses = 0
        current_consecutive_losses = 0

        for trade in self.closed_trades:
            if trade['pnl'] > 0:
                current_consecutive_wins += 1
                current_consecutive_losses = 0
            else:
                current_consecutive_losses += 1
                current_consecutive_wins = 0
            max_consecutive_wins = max(max_consecutive_wins, current_consecutive_wins)
            max_consecutive_losses = max(max_consecutive_losses, current_consecutive_losses)
        
        metrics["Max Consecutive Wins"] = max_consecutive_wins
        metrics["Max Consecutive Losses"] = max_consecutive_losses

        # Average Trade Duration
        winning_durations = [t['duration'] for t in winning_trades]
        losing_durations = [t['duration'] for t in losing_trades]

        metrics["Average Winning Trade Duration (Days)"] = np.mean(winning_durations) if winning_durations else 0.0
        metrics["Average Losing Trade Duration (Days)"] = np.mean(losing_durations) if losing_durations else 0.0
        metrics["Average Trade Duration (Days)"] = np.mean([t['duration'] for t in self.closed_trades]) if self.closed_trades else 0.0

        metrics["Total Commission Paid"] = sum(t['commission'] for t in self.closed_trades) # This assumes commission is tracked per trade

        # Market Exposure (simplified - total time in market where a position was held)
        # This is a rough estimate and can be more complex depending on how 'all_positions' is structured
        total_market_days = 0
        if self.portfolio.all_positions:
            positions_df = pd.DataFrame(self.portfolio.all_positions)
            # Ensure 'datetime' column is datetime type for proper indexing
            positions_df['datetime'] = pd.to_datetime(positions_df['datetime'])
            positions_df = positions_df.set_index("datetime")

            for symbol in self.portfolio.symbol_list:
                # Assuming non-zero position means exposure
                # Check if the symbol column exists before trying to access it
                if symbol in positions_df.columns:
                    exposed_days = positions_df[positions_df[symbol] != 0].index.to_series().diff().dt.days.sum()
                    total_market_days += exposed_days if not pd.isna(exposed_days) else 0
        metrics["Total Market Exposure (Days)"] = total_market_days


        return metrics

    def _create_plotting_index(self, datetime_index):
        """
        Creates a continuous numerical index for plotting, mapping original datetimes.
        Returns the numerical index and a dictionary for tick mapping.
        """
        unique_dates = datetime_index.unique().sort_values()
        # Create a mapping from original datetime to a continuous numerical scale
        date_to_num = {date: i for i, date in enumerate(unique_dates)}
        num_to_date = {i: date for i, date in enumerate(unique_dates)}

        # Generate tick values and labels for the plot
        # Choose a reasonable number of ticks, e.g., 10-15
        num_ticks = min(len(unique_dates), 15)
        tick_indices = np.linspace(0, len(unique_dates) - 1, num_ticks, dtype=int)
        tick_vals = [date_to_num[unique_dates[i]] for i in tick_indices]
        tick_text = [unique_dates[i].strftime('%Y-%m-%d') for i in tick_indices]

        return np.array([date_to_num[d] for d in datetime_index]), tick_vals, tick_text

    def generate_equity_curve_matplotlib(self, filepath):
        """
        Generates and saves a static Matplotlib equity curve plot.
        """
        if not self.equity_curve.empty:
            plot_index, tick_vals, tick_text = self._create_plotting_index(self.equity_curve.index)

            plt.figure(figsize=(12, 6))
            plt.plot(plot_index, self.equity_curve["equity_curve"], label="Equity Curve")
            plt.title("Equity Curve")
            plt.xlabel("Date")
            plt.ylabel("Portfolio Value")
            plt.xticks(tick_vals, tick_text, rotation=45, ha='right')
            plt.grid(True)
            plt.legend()
            plt.tight_layout()
            plt.savefig(filepath)
            plt.close()

    def generate_drawdown_matplotlib(self, filepath):
        """
        Generates and saves a static Matplotlib drawdown plot.
        """
        if not self.equity_curve.empty:
            peak = self.equity_curve["equity_curve"].expanding(min_periods=1).max()
            drawdown = (self.equity_curve["equity_curve"] - peak) / peak * 100
            plot_index, tick_vals, tick_text = self._create_plotting_index(drawdown.index)

            plt.figure(figsize=(12, 6))
            plt.fill_between(plot_index, drawdown, 0, color='red', alpha=0.5)
            plt.title("Drawdown")
            plt.xlabel("Date")
            plt.ylabel("Drawdown (%)")
            plt.xticks(tick_vals, tick_text, rotation=45, ha='right')
            plt.grid(True)
            plt.tight_layout()
            plt.savefig(filepath)
            plt.close()

    def generate_equity_curve_plotly(self, filepath):
        """
        Generates and saves an interactive Plotly equity curve plot.
        """
        if not self.equity_curve.empty:
            plot_index, tick_vals, tick_text = self._create_plotting_index(self.equity_curve.index)

            fig = go.Figure(data=[go.Scatter(x=plot_index, y=self.equity_curve["equity_curve"], mode='lines', name='Equity Curve')])
            fig.update_layout(
                title='Interactive Equity Curve',
                xaxis=dict(
                    title='Date',
                    type='linear', # Use linear type for numerical x-axis
                    tickmode='array',
                    tickvals=tick_vals,
                    ticktext=tick_text
                ),
                yaxis_title='Portfolio Value'
            )
            fig.write_html(filepath)

    def generate_drawdown_plotly(self, filepath):
        """
        Generates and saves an interactive Plotly drawdown plot.
        """
        if not self.equity_curve.empty:
            peak = self.equity_curve["equity_curve"].expanding(min_periods=1).max()
            drawdown = (self.equity_curve["equity_curve"] - peak) / peak * 100
            plot_index, tick_vals, tick_text = self._create_plotting_index(drawdown.index)

            fig = go.Figure(data=[go.Scatter(x=plot_index, y=drawdown, fill='tozeroy', mode='lines', name='Drawdown', fillcolor='rgba(255,0,0,0.5)')])
            fig.update_layout(
                title='Interactive Drawdown',
                xaxis=dict(
                    title='Date',
                    type='linear',
                    tickmode='array',
                    tickvals=tick_vals,
                    ticktext=tick_text
                ),
                yaxis_title='Drawdown (%)'
            )
            fig.write_html(filepath)

    def generate_trades_plotly(self, filepath):
        """
        Generates and saves an interactive Plotly plot showing trades overlaid on price data.
        """
        if not self.closed_trades:
            logger.info("No closed trades to plot.")
            return

        # Get all unique symbols traded
        symbols = list(set([trade['symbol'] for trade in self.closed_trades]))

        # Determine the overall date range for fetching data
        min_date = min(trade['entry_time'] for trade in self.closed_trades)
        max_date = max(trade['exit_time'] for trade in self.closed_trades)
        # Add some buffer to the date range
        min_date = min_date - timedelta(days=5)
        max_date = max_date + timedelta(days=5)

        fig = go.Figure()

        for symbol in symbols:
            # Fetch historical data for the symbol within the date range
            # This assumes data_handler can provide historical bars for a date range
            # You might need to adjust data_handler.get_latest_bars or add a new method
            # For now, let's simulate fetching historical data
            # In a real scenario, you'd call something like: self.data_handler.get_historical_bars(symbol, min_date, max_date)
            
            # For demonstration, let's use the data handler's internal symbol_data if available
            # This is a simplification and might not work directly if symbol_data is an iterator
            try:
                # Use the data_handler's public method to get the full historical data
                historical_df = self.data_handler.get_bars(symbol)
                if historical_df.empty:
                    print(f"No historical data returned for {symbol}")
                    continue
                
                # Filter the DataFrame for the required date range
                historical_df = historical_df[(historical_df.index >= min_date) & (historical_df.index <= max_date)]

            except Exception as e:
                logger.error(f"Could not retrieve historical data for {symbol}: {e}", exc_info=True)
                continue # Skip this symbol if data cannot be fetched

            if historical_df.empty:
                logger.warning(f"No historical data for {symbol} in the specified range.")
                continue

            # Plot candlestick chart
            plot_index, tick_vals, tick_text = self._create_plotting_index(historical_df.index)
            
            # Map original datetimes to numerical plot index
            date_to_num_map = {date: i for i, date in enumerate(historical_df.index.unique().sort_values())}

            fig.add_trace(go.Candlestick(
                x=plot_index,
                open=historical_df['open'],
                high=historical_df['high'],
                low=historical_df['low'],
                close=historical_df['close'],
                name=f'{symbol} Price'
            ))

            # Add trade markers
            for trade in self.closed_trades:
                if trade['symbol'] == symbol:
                    entry_num = date_to_num_map.get(trade['entry_time'])
                    exit_num = date_to_num_map.get(trade['exit_time'])

                    if entry_num is not None:
                        # Entry marker
                        fig.add_trace(go.Scatter(
                            x=[entry_num],
                            y=[trade['entry_price']],
                            mode='markers',
                            marker=dict(symbol='triangle-up' if trade['direction'] == 'LONG' else 'triangle-down', size=10, color='green'),
                            name=f'{symbol} Entry', showlegend=False,
                            hoverinfo='text',
                            hovertext=f'Entry: {trade['entry_time']}<br>Price: {trade['entry_price']:.2f}<br>Qty: {trade['quantity']}<br>Dir: {trade['direction']}'
                        ))
                    if exit_num is not None:
                        # Exit marker
                        fig.add_trace(go.Scatter(
                            x=[exit_num],
                            y=[trade['exit_price']],
                            mode='markers',
                            marker=dict(symbol='circle' if trade['pnl'] > 0 else 'x', size=10, color='blue' if trade['pnl'] > 0 else 'red'),
                            name=f'{symbol} Exit', showlegend=False,
                            hoverinfo='text',
                            hovertext=f'Exit: {trade['exit_time']}<br>Price: {trade['exit_price']:.2f}<br>PnL: {trade['pnl']:.2f}<br>Duration: {trade['duration']:.2f} days'
                        ))

        fig.update_layout(
            title='Interactive Trades Overlay',
            xaxis=dict(
                title='Date',
                type='linear',
                tickmode='array',
                tickvals=tick_vals,
                ticktext=tick_text
            ),
            yaxis_title='Price',
            xaxis_rangeslider_visible=False
        )
        fig.write_html(filepath)