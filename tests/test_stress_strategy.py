import unittest
import datetime
import os

from backtester import Backtester
from data_handler import CSVDataHandler
from portfolio import Portfolio
from execution_handler import SimulatedExecutionHandler
from strategy import StressTestStrategy

class TestStressStrategy(unittest.TestCase):
    def setUp(self):
        # Create mock CSV data
        self.csv_dir = './data'
        self.symbol = 'STRESSTEST'
        self.csv_path = os.path.join(self.csv_dir, f'{self.symbol}.csv')
        os.makedirs(self.csv_dir, exist_ok=True)
        with open(self.csv_path, 'w') as f:
            f.write("Date,open,high,low,close,volume\n")
            f.write("2023-01-01,100,101,99,100,1000\n")
            f.write("2023-01-02,100,102,100,101,1000\n")
            f.write("2023-01-03,101,101,95,96,1000\n")
            f.write("2023-01-04,96,98,95,97,1000\n")
            f.write("2023-01-05,97,105,95,104,1000\n")
            f.write("2023-01-06,104,105,102,103,1000\n")
            f.write("2023-01-07,103,103,98,99,1000\n")
            f.write("2023-01-08,99,101,99,100,1000\n")
            f.write("2023-01-09,100,102,100,101,1000\n")
            f.write("2023-01-10,101,101,100,100,1000\n")
            f.write("2023-01-11,100,101,99,100,1000\n")
            f.write("2023-01-11,100,101,99,100,1000\n")

        self.symbol_list = [self.symbol]
        self.initial_capital = 100000.0
        self.start_date = datetime.datetime(2023, 1, 1)
        self.heartbeat = 0.0

    def tearDown(self):
        # Clean up the mock CSV file
        os.remove(self.csv_path)

    def test_stress_strategy_execution(self):
        # Run the backtest
        backtester = Backtester(
            self.csv_dir,
            self.symbol_list,
            self.initial_capital,
            self.start_date,
            self.heartbeat,
            CSVDataHandler,
            SimulatedExecutionHandler,
            Portfolio,
            StressTestStrategy
        )
        backtester.simulate_trading()

        # --- Verification ---
        portfolio = backtester.portfolio
        trades = portfolio.closed_trades

        # Expected trades based on the StressTestStrategy and mock data
        # Note: These values may need slight adjustments based on commission and exact execution logic

        self.assertEqual(len(trades), 3)

        # Trade 1: Stop-loss on the initial long position
        self.assertAlmostEqual(trades[0]['entry_price'], 100.65, delta=0.1)
        self.assertEqual(trades[0]['exit_price'], 95.0)
        self.assertEqual(trades[0]['quantity'], 114)
        self.assertEqual(trades[0]['direction'], 'LONG')

        # Trade 2: Trailing stop on the short position
        self.assertEqual(trades[1]['entry_price'], 104.0)
        self.assertEqual(trades[1]['exit_price'], 101.0) # Trailing stop triggers at 101
        self.assertEqual(trades[1]['quantity'], 30)
        self.assertEqual(trades[1]['direction'], 'SHORT')

        # Trade 3: Final exit of the small long position
        self.assertEqual(trades[2]['entry_price'], 99.0)
        self.assertEqual(trades[2]['exit_price'], 100.0)
        self.assertEqual(trades[2]['quantity'], 5)
        self.assertEqual(trades[2]['direction'], 'LONG')

if __name__ == '__main__':
    unittest.main()
