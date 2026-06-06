from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.dialects.postgresql import insert
from neo4j import AsyncGraphDatabase
from typing import List

from models.schemas.ingest import TransactionRow
from models.sql.account import Account
from models.sql.transaction import Transaction

class GraphWriter:
    def __init__(self, pg_session: AsyncSession, neo4j_uri: str, neo4j_user: str, neo4j_pass: str):
        self.pg_session = pg_session
        self.neo4j_driver = AsyncGraphDatabase.driver(neo4j_uri, auth=(neo4j_user, neo4j_pass))

    async def close(self):
        await self.neo4j_driver.close()

    async def write_batch(self, rows: List[TransactionRow], case_id: str = None):
        if not rows:
            return

        # 1. PostgreSQL Relational Write (Bulk)
        # Prepare accounts
        accounts_data = []
        unique_accounts = set()
        for r in rows:
            if r.from_account not in unique_accounts:
                accounts_data.append({"account_number": r.from_account, "account_label": "unknown"})
                unique_accounts.add(r.from_account)
            if r.to_account not in unique_accounts:
                accounts_data.append({"account_number": r.to_account, "account_label": "unknown"})
                unique_accounts.add(r.to_account)

        # Upsert Accounts (DO NOTHING ON CONFLICT to avoid duplicate key errors)
        if accounts_data:
            stmt_acc = insert(Account).values(accounts_data)
            stmt_acc = stmt_acc.on_conflict_do_nothing(index_elements=['account_number'])
            await self.pg_session.execute(stmt_acc)

        # Prepare transactions
        tx_data = [
            {
                "transaction_ref": r.transaction_ref,
                "from_account": r.from_account,
                "to_account": r.to_account,
                "amount": r.amount,
                "currency": r.currency,
                "timestamp": r.timestamp,
                "transaction_type": r.transaction_type,
                "upi_id": r.upi_id,
                "narration": r.narration,
                "risk_flag": r.risk_flag,
                "case_id": case_id
            }
            for r in rows
        ]

        # Insert Transactions (DO NOTHING ON CONFLICT for idempotency)
        stmt_tx = insert(Transaction).values(tx_data)
        stmt_tx = stmt_tx.on_conflict_do_nothing(index_elements=['transaction_ref'])
        await self.pg_session.execute(stmt_tx)
        
        # Commit PostgreSQL transaction to ensure relational integrity before Neo4j
        await self.pg_session.commit()

        # 2. Neo4j Graph Write (UNWIND for high performance batch insert)
        cypher_query = """
        UNWIND $batch AS tx
        
        // Merge Sender
        MERGE (sender:Account {accountNumber: tx.from_account})
        ON CREATE SET sender.createdAt = datetime()
        
        // Merge Receiver
        MERGE (receiver:Account {accountNumber: tx.to_account})
        ON CREATE SET receiver.createdAt = datetime()
        
        // Merge Transaction Edge
        MERGE (sender)-[r:SENT {transactionRef: tx.transaction_ref}]->(receiver)
        ON CREATE SET 
            r.amount = tx.amount,
            r.timestamp = datetime(tx.timestamp_str),
            r.transactionType = tx.transaction_type,
            r.upiId = tx.upi_id,
            r.riskFlag = tx.risk_flag
        """
        
        # Format datetimes to ISO strings for Neo4j consumption
        neo4j_batch = [
            {**r.model_dump(), "timestamp_str": r.timestamp.isoformat()}
            for r in rows
        ]

        async with self.neo4j_driver.session() as session:
            await session.run(cypher_query, batch=neo4j_batch)
