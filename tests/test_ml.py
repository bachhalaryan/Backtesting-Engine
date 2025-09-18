import unittest
import pandas as pd
from analysis.ml import (
    create_lagged_features, create_target_binary, create_target_regression,
    train_model, predict_with_model, evaluate_regression_model,
    train_model_with_cv, predict_baseline_mid_price
)
from sklearn.ensemble import RandomForestClassifier, GradientBoostingRegressor
from sklearn.linear_model import LogisticRegression, LinearRegression
from sklearn.metrics import mean_absolute_error, r2_score
import numpy as np

class TestMLAnalysis(unittest.TestCase):

    def setUp(self):
        # Create a dummy DataFrame for testing
        self.data = {
            'Date': pd.to_datetime([
                '2023-01-01', '2023-01-02', '2023-01-03', '2023-01-04', '2023-01-05',
                '2023-01-06', '2023-01-07', '2023-01-08', '2023-01-09', '2023-01-10',
                '2023-01-11', '2023-01-12', '2023-01-13', '2023-01-14', '2023-01-15',
                '2023-01-16', '2023-01-17', '2023-01-18', '2023-01-19', '2023-01-20',
            ]),
            'Close': [
                10, 11, 12, 11, 13, 14, 13, 15, 16, 15,
                17, 18, 19, 18, 20, 21, 20, 22, 23, 22,
            ],
            'High': [
                10.5, 11.5, 12.5, 11.5, 13.5, 14.5, 13.5, 15.5, 16.5, 15.5,
                17.5, 18.5, 19.5, 18.5, 20.5, 21.5, 20.5, 22.5, 23.5, 22.5,
            ],
            'Low': [
                9.5, 10.5, 11.5, 10.5, 12.5, 13.5, 12.5, 14.5, 15.5, 14.5,
                16.5, 17.5, 18.5, 17.5, 19.5, 20.5, 19.5, 21.5, 22.5, 21.5,
            ]
        }
        self.df = pd.DataFrame(self.data).set_index('Date')

    def test_create_lagged_features(self):
        lags = [1, 2]
        features = create_lagged_features(self.df, lags, target_column='Close')
        self.assertIsInstance(features, pd.DataFrame)
        self.assertIn('Close_lag_1', features.columns)
        self.assertIn('Close_lag_2', features.columns)
        self.assertEqual(len(features), len(self.df) - max(lags))
        self.assertEqual(features.loc['2023-01-03', 'Close_lag_1'], 11) # Close on 2023-01-02
        self.assertEqual(features.loc['2023-01-03', 'Close_lag_2'], 10) # Close on 2023-01-01

    def test_create_target_binary(self):
        target = create_target_binary(self.df, column='Close', periods=1)
        self.assertIsInstance(target, pd.Series)
        self.assertEqual(len(target), len(self.df) - 1) # One less due to shift(-1).dropna()
        self.assertEqual(target.loc['2023-01-01'], 1) # 11 > 10
        self.assertEqual(target.loc['2023-01-03'], 0) # 11 is not > 12
        self.assertEqual(target.loc['2023-01-04'], 1) # 13 > 11

    def test_create_target_regression(self):
        target = create_target_regression(self.df, column='Close', periods=1)
        self.assertIsInstance(target, pd.Series)
        self.assertEqual(len(target), len(self.df) - 1)
        self.assertEqual(target.loc['2023-01-01'], 11) # Next day's close
        self.assertEqual(target.loc['2023-01-19'], 22) # Last valid target

    def test_train_model_classification(self):
        lags = [1]
        features = create_lagged_features(self.df, lags, target_column='Close')
        target = create_target_binary(self.df, column='Close', periods=1)
        
        common_index = features.index.intersection(target.index)
        X = features.loc[common_index]
        y = target.loc[common_index]

        model, metrics = train_model(X, y, model=LogisticRegression(random_state=42, solver='liblinear'), is_regression=False)
        self.assertIsNotNone(model)
        self.assertIn('accuracy', metrics)
        self.assertIsInstance(metrics['accuracy'], float)
        self.assertGreaterEqual(metrics['accuracy'], 0.0)
        self.assertLessEqual(metrics['accuracy'], 1.0)

    def test_train_model_regression(self):
        lags = [1]
        features = create_lagged_features(self.df, lags, target_column='Close')
        target = create_target_regression(self.df, column='Close', periods=1)
        
        common_index = features.index.intersection(target.index)
        X = features.loc[common_index]
        y = target.loc[common_index]

        model, metrics = train_model(X, y, model=LinearRegression(), is_regression=True)
        self.assertIsNotNone(model)
        self.assertIn('mae', metrics)
        self.assertIn('r2', metrics)
        self.assertIsInstance(metrics['mae'], float)

    def test_evaluate_regression_model(self):
        y_true = pd.Series([10, 11, 12])
        y_pred = np.array([10.1, 10.9, 12.2])
        metrics = evaluate_regression_model(y_true, y_pred)
        self.assertIn('mae', metrics)
        self.assertIn('rmse', metrics)
        self.assertIn('r2', metrics)
        self.assertAlmostEqual(metrics['mae'], 0.133, places=3)
        self.assertAlmostEqual(metrics['r2'], 0.970, places=3)

    def test_train_model_with_cv(self):
        lags = [1]
        features = create_lagged_features(self.df, lags, target_column='Close')
        target = create_target_regression(self.df, column='Close', periods=1)
        
        common_index = features.index.intersection(target.index)
        X = features.loc[common_index]
        y = target.loc[common_index]

        model = LinearRegression()
        last_model, fold_metrics = train_model_with_cv(X, y, model, n_splits=3, is_regression=True)
        
        self.assertIsNotNone(last_model)
        self.assertIn('mae', fold_metrics)
        self.assertEqual(len(fold_metrics['mae']), 3) # n_splits
        self.assertIsInstance(fold_metrics['mae'][0], float)

    def test_predict_with_model(self):
        lags = [1]
        features = create_lagged_features(self.df, lags, target_column='Close')
        target = create_target_binary(self.df, column='Close', periods=1)
        
        common_index = features.index.intersection(target.index)
        X = features.loc[common_index]
        y = target.loc[common_index]

        model, _ = train_model(X, y, model=RandomForestClassifier(n_estimators=10, random_state=42))
        predictions = predict_with_model(model, X)
        
        self.assertIsInstance(predictions, pd.Series)
        self.assertEqual(len(predictions), len(X))
        self.assertTrue(all(p in [0, 1] for p in predictions)) # Binary predictions

    def test_predict_baseline_mid_price(self):
        # Create a DataFrame with mid_price
        df_with_mid = self.df.copy()
        df_with_mid['mid_price'] = (df_with_mid['High'] + df_with_mid['Low']) / 2

        baseline_predictions = predict_baseline_mid_price(df_with_mid, column='mid_price', periods=1)
        self.assertIsInstance(baseline_predictions, pd.Series)
        self.assertEqual(len(baseline_predictions), len(self.df) - 1)
        # Prediction for 2023-01-01 should be 2023-01-01's mid_price
        self.assertEqual(baseline_predictions.loc['2023-01-01'], df_with_mid.loc['2023-01-01', 'mid_price'])
        self.assertEqual(baseline_predictions.loc['2023-01-19'], df_with_mid.loc['2023-01-19', 'mid_price'])

if __name__ == '__main__':
    unittest.main()
