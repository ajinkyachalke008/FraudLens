"""
Cross-Bank Layering Detector — Detects rapid transfers across multiple banks.
Money bouncing through 3+ different banks within 24 hours is a classic
layering technique used to obscure the money trail.

Uses Neo4j when available, falls back to SQL analysis.
"""
import logging
from datetime import datetime, timedelta
from sqlalchemy import select, func, or_, distinct
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

# Bank identification from IFSC prefix (first 4 chars)
IFSC_BANK_MAP = {
    'HDFC': 'HDFC Bank', 'SBIN': 'SBI', 'ICIC': 'ICICI Bank', 'UTIB': 'Axis Bank',
    'PUNB': 'PNB', 'CNRB': 'Canara Bank', 'BARB': 'Bank of Baroda', 'UBIN': 'Union Bank',
    'KKBK': 'Kotak Mahindra', 'YESB': 'Yes Bank', 'IDFB': 'IDFC First', 'IBKL': 'IDBI Bank',
    'FDRL': 'Federal Bank', 'INDB': 'IndusInd Bank', 'BKID': 'Bank of India',
    'UCBA': 'UCO Bank', 'IOBA': 'Indian Overseas', 'ALLA': 'Allahabad Bank',
    'CBIN': 'Central Bank', 'ORBC': 'PNB (Oriental)', 'CORP': 'Union Bank (Corp)',
    'ANDB': 'Canara (Andhra)', 'SYNB': 'Canara (Syndicate)', 'PSIB': 'PSB',
    'MAHB': 'Bank of Maharashtra', 'KARB': 'Karnataka Bank', 'KVBL': 'KVB',
    'TMBL': 'TMB', 'JAKA': 'J&K Bank', 'SRCB': 'Saraswat Bank',
}


class CrossBankDetector:
    """
    Detects money laundering layering through multiple banks:
    - Track distinct banks touched in money trail within 24-48h
    - 3+ banks involved = layering indicator
    - Speed of cross-bank movement matters (faster = more suspicious)
    """

    BANK_THRESHOLD = 3          # 3+ distinct banks in a chain
    TIME_WINDOW_HOURS = 48     # 48-hour window for chain detection

    def __init__(self, neo4j_driver=None):
        self._neo4j = neo4j_driver
        self._evidence = {}

    async def score(self, account_id: str, db: AsyncSession) -> float:
        try:
            if self._neo4j:
                return await self._score_via_neo4j(account_id)
            else:
                return await self._score_via_sql(account_id, db)
        except Exception as e:
            logger.warning(f"CrossBankDetector error for {account_id}: {e}")
            self._evidence = {"error": str(e), "triggered": False}
            return 0.0

    async def _score_via_neo4j(self, account_id: str) -> float:
        """Neo4j: find distinct banks in multi-hop paths from this account."""
        cypher = """
        MATCH path = (a:Account {accountNumber: $id})-[:SENT*1..4]->(b:Account)
        WITH [n IN nodes(path) | n.bank] AS banks
        UNWIND banks AS bank
        WITH DISTINCT bank WHERE bank IS NOT NULL
        RETURN collect(bank) AS distinct_banks, count(bank) AS bank_count
        """
        async with self._neo4j.session() as session:
            result = await session.run(cypher, id=account_id)
            record = await result.single()

        if not record or record["bank_count"] < self.BANK_THRESHOLD:
            self._evidence = {"distinct_banks": record["bank_count"] if record else 0, "triggered": False, "mode": "neo4j"}
            return 0.0

        bank_count = record["bank_count"]
        banks = record["distinct_banks"]
        score = min((bank_count - self.BANK_THRESHOLD + 1) / 4, 1.0)

        self._evidence = {
            "distinct_banks": bank_count,
            "banks_involved": banks[:10],
            "triggered": True,
            "mode": "neo4j"
        }
        return round(score, 3)

    async def _score_via_sql(self, account_id: str, db: AsyncSession) -> float:
        """SQL fallback: estimate bank diversity from account number patterns."""
        from models.sql.transaction import Transaction

        now = datetime.utcnow()
        window = now - timedelta(hours=self.TIME_WINDOW_HOURS)

        # Get all counterparty accounts in the time window
        result = await db.execute(
            select(Transaction.from_account, Transaction.to_account).where(
                or_(
                    Transaction.from_account == account_id,
                    Transaction.to_account == account_id
                ),
                Transaction.timestamp >= window
            )
        )
        rows = result.all()

        # Collect all unique accounts in the chain
        accounts = set()
        for row in rows:
            accounts.add(row[0])
            accounts.add(row[1])
        accounts.discard(account_id)

        # 2nd-degree: get counterparties of counterparties
        if accounts:
            acc_list = list(accounts)[:50]  # Limit for performance
            result2 = await db.execute(
                select(Transaction.from_account, Transaction.to_account).where(
                    or_(
                        Transaction.from_account.in_(acc_list),
                        Transaction.to_account.in_(acc_list)
                    ),
                    Transaction.timestamp >= window
                ).limit(200)
            )
            for row in result2.all():
                accounts.add(row[0])
                accounts.add(row[1])

        # Estimate bank diversity from account prefixes
        # In reality, IFSC codes would be stored; here we approximate
        bank_prefixes = set()
        for acc in accounts:
            # Try to extract bank hint from account format
            if len(acc) >= 4:
                prefix = acc[:4].upper()
                if prefix in IFSC_BANK_MAP:
                    bank_prefixes.add(IFSC_BANK_MAP[prefix])
                else:
                    bank_prefixes.add(f"BANK-{prefix}")

        distinct_banks = len(bank_prefixes)

        if distinct_banks < self.BANK_THRESHOLD:
            self._evidence = {
                "distinct_banks": distinct_banks,
                "accounts_in_chain": len(accounts),
                "triggered": False,
                "mode": "sql_estimate"
            }
            return 0.0

        score = min((distinct_banks - self.BANK_THRESHOLD + 1) / 5, 1.0)

        self._evidence = {
            "distinct_banks": distinct_banks,
            "banks_estimated": list(bank_prefixes)[:10],
            "accounts_in_chain": len(accounts),
            "triggered": True,
            "mode": "sql_estimate"
        }
        return round(score, 3)

    def get_evidence(self) -> dict:
        return self._evidence
