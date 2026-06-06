import asyncio
import uuid
import random
import os
import sys
from datetime import datetime

# Add the project root to the python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.database import AsyncSessionLocal
from core.security import get_password_hash
from models.sql.user import User
from models.sql.account import Account
from models.sql.transaction import Transaction
from models.sql.case import Case
from core.database import get_db

async def seed_data():
    from core.database import init_db
    await init_db()
    async for session in get_db():
        print("Starting data seeding (Phase 6)...")
        from sqlalchemy import text
        await session.execute(text("DELETE FROM transactions;"))
        await session.execute(text("DELETE FROM cases;"))
        await session.execute(text("DELETE FROM accounts;"))
        await session.execute(text("DELETE FROM users;"))
        await session.commit()
        
        # --- 1. SEED USERS ---
        users_data = [
            {
                "email": "admin@fraudlens.gov",
                "full_name": "System Admin",
                "role": "admin",
                "badge_number": "ADM-001",
                "department": "IT Operations"
            },
            {
                "email": "investigator@fraudlens.gov",
                "full_name": "Lead Inspector",
                "role": "investigator",
                "badge_number": "INV-774",
                "department": "Cyber Cell"
            },
            {
                "email": "analyst@fraudlens.gov",
                "full_name": "Data Analyst",
                "role": "analyst",
                "badge_number": "ANA-202",
                "department": "Financial Intelligence"
            },
            {
                "email": "viewer@fraudlens.gov",
                "full_name": "Guest Viewer",
                "role": "viewer",
                "badge_number": "GST-000",
                "department": "Auditing"
            }
        ]

        password_hash = get_password_hash("fraudlens2026")
        for u in users_data:
            user = User(
                id=uuid.uuid4(),
                email=u["email"],
                password_hash=password_hash,
                full_name=u["full_name"],
                role=u["role"],
                badge_number=u["badge_number"],
                department=u["department"]
            )
            session.add(user)
        
        await session.commit()
        print("Users seeded successfully.")

        # --- 2. SEED ACCOUNTS & TRANSACTIONS ---
        accounts = []
        for i in range(5):
            acc = Account(
                id=uuid.uuid4(),
                account_number=f"ACC-00{i+1}",
                registered_name=f"Demo Account {i+1}",
                account_type="Savings",
                state="MH",
                ifsc_code="HDFC0001"
            )
            session.add(acc)
            accounts.append(acc)
        
        await session.commit()

        # Seed a dummy critical case
        case_id = uuid.uuid4()
        case = Case(
            id=case_id,
            case_number=f"CAS-{str(case_id)[:8].upper()}",
            title="Automated Syndicate Detection #1",
            status="open",
            priority="critical",
            description="Initial seed data case",
            total_amount=150000.0,
            victim_count=2,
            suspect_count=3,
        )
        session.add(case)
        await session.commit()

        # Seed some transactions
        if len(accounts) >= 2:
            txn1 = Transaction(
                id=uuid.uuid4(),
                transaction_ref="TXN-001",
                from_account=accounts[0].account_number,
                to_account=accounts[1].account_number,
                amount=50000.0,
                transaction_type="IMPS",
                risk_flag="high",
                case_id=case_id,
                timestamp=datetime.utcnow()
            )
            session.add(txn1)
        
        await session.commit()
        print("Accounts, Cases, and Transactions seeded.")

    print("Data seeding complete! You can log in with investigator@fraudlens.gov / fraudlens2026")

if __name__ == "__main__":
    asyncio.run(seed_data())
