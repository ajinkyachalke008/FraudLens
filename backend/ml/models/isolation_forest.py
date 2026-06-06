import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
import numpy as np
import joblib
import os

class TransactionAnomalyDetector:
    """
    Scikit-Learn Isolation Forest wrapper for detecting anomalous individual transactions.
    Catches "out-of-character" behaviors immediately without full graph traversal.
    """
    def __init__(self, contamination: float = 0.05, model_path: str = "isolation_forest.joblib"):
        # contamination sets the expected proportion of outliers (5%)
        self.model = IsolationForest(
            n_estimators=100, 
            max_samples='auto', 
            contamination=contamination, 
            random_state=42
        )
        self.scaler = StandardScaler()
        self.is_trained = False
        self.feature_columns = ['amount', 'hour_of_day', 'velocity_1h', 'velocity_24h']
        self.model_path = model_path

    def train(self, df: pd.DataFrame):
        """
        Trains the isolation forest on historical transaction data with scaling.
        """
        if df.empty or len(df) < 10:
            raise ValueError("Insufficient data to train Isolation Forest")
            
        X = df[self.feature_columns].fillna(0)
        X_scaled = self.scaler.fit_transform(X)
        
        self.model.fit(X_scaled)
        self.is_trained = True
        self.save_model()

    def save_model(self):
        """Persists the trained model and scaler to disk."""
        joblib.dump({'model': self.model, 'scaler': self.scaler}, self.model_path)

    def load_model(self):
        """Loads a trained model and scaler from disk."""
        if os.path.exists(self.model_path):
            data = joblib.load(self.model_path)
            self.model = data['model']
            self.scaler = data['scaler']
            self.is_trained = True

    def predict(self, df: pd.DataFrame) -> list[dict]:
        """
        Predicts anomalies for new transactions.
        Returns a list of dicts with risk_score and is_anomaly flag.
        """
        if not self.is_trained:
            self.load_model()
            
        if not self.is_trained:
            # Fallback mock prediction if model isn't trained yet
            return self._mock_predict(df)
            
        X = df[self.feature_columns].fillna(0)
        X_scaled = self.scaler.transform(X)
        
        # predict returns 1 for inliers, -1 for outliers
        predictions = self.model.predict(X_scaled)
        
        # score_samples returns opposite of anomaly score (lower is more anomalous)
        # Convert to a 0-1 risk score (1 being highly anomalous)
        scores = self.model.score_samples(X_scaled)
        risk_scores = np.clip(0.5 - (scores / 2), 0.0, 1.0)
        
        results = []
        for i in range(len(df)):
            results.append({
                "transaction_id": df.iloc[i].get("id", f"txn_{i}"),
                "is_anomaly": bool(predictions[i] == -1),
                "anomaly_risk_score": float(risk_scores[i])
            })
            
        return results

    def _mock_predict(self, df: pd.DataFrame) -> list[dict]:
        """Returns mock risk scores based on hardcoded heuristics for testing."""
        results = []
        for i in range(len(df)):
            amount = df.iloc[i].get('amount', 0)
            velocity = df.iloc[i].get('velocity_1h', 0)
            
            # Simple heuristic: high amount + high velocity = anomaly
            risk = 0.1
            if amount > 500000: risk += 0.5
            if velocity > 10: risk += 0.3
            
            results.append({
                "transaction_id": df.iloc[i].get("id", f"txn_{i}"),
                "is_anomaly": risk > 0.6,
                "anomaly_risk_score": min(risk, 1.0)
            })
        return results
