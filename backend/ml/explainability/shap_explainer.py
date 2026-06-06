import shap
import pandas as pd
import numpy as np

class FraudExplainer:
    """
    Generates human-readable explanations for ML model predictions.
    Law enforcement needs to know *why* an account or transaction was flagged.
    """
    def __init__(self, model, feature_names: list[str]):
        self.model = model
        self.feature_names = feature_names
        self.explainer = None
        
        # If the model is an sklearn IsolationForest, we can use TreeExplainer
        if model and hasattr(model, 'estimators_'):
            try:
                # TreeExplainer is experimental for IsolationForest but works for basic feature attr
                self.explainer = shap.TreeExplainer(model)
            except Exception:
                self.explainer = None
        
    def generate_explanation(self, features: dict) -> dict:
        """
        Mock SHAP explanation generator for the frontend UI.
        Real SHAP requires calculating baseline expected values.
        """
        # Convert to DataFrame
        df = pd.DataFrame([features])
        
        explanations = []
        base_risk = 0.0
        
        # If we have a real SHAP explainer loaded, use it
        if self.explainer is not None:
            shap_values = self.explainer.shap_values(df)
            
            # For Isolation Forest, negative SHAP values often mean more anomalous
            # We take absolute value for importance
            importances = np.abs(shap_values[0])
            
            for idx, feature_name in enumerate(self.feature_names):
                if feature_name in features and importances[idx] > 0:
                    explanations.append({
                        "feature": feature_name,
                        "importance": float(importances[idx]),
                        "description": f"Feature '{feature_name}' (value: {features[feature_name]}) significantly shifted the model prediction."
                    })
                    base_risk += float(importances[idx])
        else:
            # Simulated heuristic fallback for PyTorch GNN or offline models
            if 'velocity_1h' in features and features['velocity_1h'] > 5:
                explanations.append({
                    "feature": "velocity_1h",
                    "importance": 0.45,
                    "description": f"Rapid burst of {features['velocity_1h']} transactions in 1 hour."
                })
                base_risk += 0.45
            
        if 'amount' in features and features['amount'] > 100000:
            explanations.append({
                "feature": "amount",
                "importance": 0.35,
                "description": f"Transaction value of ₹{features['amount']} is statistically anomalous for this account profile."
            })
            base_risk += 0.35
            
        if 'degree_centrality' in features and features['degree_centrality'] > 10:
            explanations.append({
                "feature": "degree_centrality",
                "importance": 0.60,
                "description": "Account is acting as a massive central relay point (high degree centrality)."
            })
            base_risk += 0.60
            
        # Sort by importance descending
        explanations.sort(key=lambda x: x['importance'], reverse=True)
        
        return {
            "total_risk_score": min(base_risk + 0.05, 1.0),
            "top_factors": explanations[:3],  # Top 3 reasons
            "summary": "High risk detected due to rapid transaction bursts combined with high volume." if base_risk > 0.5 else "Activity appears normal."
        }
