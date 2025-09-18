import unittest
import pandas as pd
from analysis.ml import create_lagged_features, create_target_binary, train_model, predict_with_model
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression

class TestMLAnalysis(unittest.TestCase):

    def setUp(self):
        # Create a dummy DataFrame for testing
        self.data = {
            'Date': pd.to_datetime([
                '2023-01-01', '2023-01-02', '2023-01-03', '2023-01-04', '2023-01-05',
                '2023-01-06', '2023-01-07', '2023-01-08', '2023-01-09', '2023-01-10',
            ]),
            'Close': [
                10, 11, 12, 11, 13, 14, 13, 15, 16, 15,
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
        self.assertEqual(target.loc['2023-01-03'], 0) # 13 > 11 is true, but 11 is not > 12
        self.assertEqual(target.loc['2023-01-04'], 1) # 14 > 13

    def test_train_model(self):
        lags = [1]
        features = create_lagged_features(self.df, lags, target_column='Close')
        target = create_target_binary(self.df, column='Close', periods=1)
        
        # Align features and target
        common_index = features.index.intersection(target.index)
        X = features.loc[common_index]
        y = target.loc[common_index]

        model, accuracy = train_model(X, y, model=LogisticRegression(random_state=42, solver='liblinear'))
        self.assertIsNotNone(model)
        self.assertIsInstance(accuracy, float)
        self.assertGreaterEqual(accuracy, 0.0) # Accuracy should be between 0 and 1
        self.assertLessEqual(accuracy, 1.0)

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

if __name__ == '__main__':
    unittest.main()
