"""
Mule Classifier — Composite classifier that identifies financial mule accounts.
Combines velocity, shell, and structuring signals.
If 3+ individual scores > 0.6 → MULE tag.
"""
import logging
from typing import Dict

logger = logging.getLogger(__name__)


class MuleClassifier:
    MULE_THRESHOLD = 0.6
    MIN_SIGNALS_FOR_MULE = 2

    def __init__(self):
        self._evidence = {}

    def classify(self, signal_scores: Dict[str, float]) -> float:
        """
        Composite mule classification based on individual detector scores.
        
        Args:
            signal_scores: Dict with keys: velocity, structuring, shell, roundtrip, dormancy
            
        Returns:
            Composite mule score 0.0-1.0
        """
        mule_signals = ['velocity', 'shell', 'structuring', 'roundtrip']
        active_signals = []
        
        for signal in mule_signals:
            score = signal_scores.get(signal, 0.0)
            if score >= self.MULE_THRESHOLD:
                active_signals.append(signal)

        is_mule = len(active_signals) >= self.MIN_SIGNALS_FOR_MULE

        if not active_signals:
            self._evidence = {
                "active_mule_signals": 0,
                "is_mule": False,
                "triggered_signals": [],
            }
            return 0.0

        # Weighted composite of active signals
        weights = {
            'velocity': 0.30,
            'shell': 0.35,
            'structuring': 0.20,
            'roundtrip': 0.15,
        }
        
        weighted_sum = sum(
            signal_scores.get(s, 0) * weights.get(s, 0.25)
            for s in active_signals
        )
        total_weight = sum(weights.get(s, 0.25) for s in active_signals)
        composite = weighted_sum / total_weight if total_weight > 0 else 0

        # Boost if multiple signals are active
        if len(active_signals) >= 3:
            composite = min(composite * 1.2, 1.0)

        self._evidence = {
            "active_mule_signals": len(active_signals),
            "is_mule": is_mule,
            "triggered_signals": active_signals,
            "composite_score": round(composite, 3),
            "signal_scores": {s: round(signal_scores.get(s, 0), 3) for s in mule_signals}
        }
        return round(composite, 3)

    def get_evidence(self) -> dict:
        return self._evidence
