"""
Roundtrip Detector — Detects circular money flows via Neo4j graph cycles.
Falls back to mock data when Neo4j is offline.
"""
import logging

logger = logging.getLogger(__name__)

# Mock roundtrip data for offline operation
MOCK_ROUNDTRIP = {
    "ACC-1001": {"cycles_found": 2, "min_depth": 3, "max_depth": 4, "paths": [
        ["ACC-1001", "ACC-1002", "ACC-1004", "ACC-1001"],
        ["ACC-1001", "ACC-1002", "ACC-1005", "ACC-1004", "ACC-1001"],
    ]},
    "ACC-1004": {"cycles_found": 1, "min_depth": 3, "max_depth": 3, "paths": [
        ["ACC-1004", "ACC-1005", "ACC-1002", "ACC-1004"],
    ]},
}


class RoundtripDetector:
    def __init__(self, neo4j_driver=None):
        self._neo4j = neo4j_driver
        self._evidence = {}

    async def score(self, account_id: str, db=None) -> float:
        """
        Detects cycles of depth 2-5 involving this account.
        Uses Neo4j Cypher when available, mock data otherwise.
        """
        try:
            if self._neo4j:
                return await self._score_live(account_id)
            else:
                return self._score_mock(account_id)
        except Exception as e:
            logger.warning(f"RoundtripDetector error for {account_id}: {e}")
            self._evidence = {"error": str(e), "triggered": False}
            return 0.0

    async def _score_live(self, account_id: str) -> float:
        """Live Neo4j cycle detection."""
        cypher = """
        MATCH path = (a:Account {accountNumber: $id})-[:SENT*2..5]->(a)
        RETURN length(path) as cycle_depth, 
               [n IN nodes(path) | n.accountNumber] as accounts
        ORDER BY cycle_depth ASC
        LIMIT 10
        """
        async with self._neo4j.session() as session:
            result = await session.run(cypher, id=account_id)
            records = await result.data()

        if not records:
            self._evidence = {"cycles_found": 0, "triggered": False}
            return 0.0

        cycles = len(records)
        min_depth = min(r["cycle_depth"] for r in records)
        max_depth = max(r["cycle_depth"] for r in records)

        # Score: more cycles and shorter cycles = higher risk
        score = min(cycles / 5, 1.0) * (1.0 - (min_depth - 2) / 5)
        score = max(0, min(score, 1.0))

        self._evidence = {
            "cycles_found": cycles,
            "min_depth": min_depth,
            "max_depth": max_depth,
            "paths": [r["accounts"] for r in records[:3]],
            "triggered": score > 0.4
        }
        return round(score, 3)

    def _score_mock(self, account_id: str) -> float:
        """Mock fallback with pre-built cycle data."""
        data = MOCK_ROUNDTRIP.get(account_id)
        if not data:
            self._evidence = {"cycles_found": 0, "triggered": False, "mode": "mock"}
            return 0.0

        cycles = data["cycles_found"]
        min_depth = data["min_depth"]
        score = min(cycles / 5, 1.0) * (1.0 - (min_depth - 2) / 5)
        score = max(0, min(score, 1.0))

        self._evidence = {**data, "triggered": score > 0.4, "mode": "mock"}
        return round(score, 3)

    def get_evidence(self) -> dict:
        return self._evidence
