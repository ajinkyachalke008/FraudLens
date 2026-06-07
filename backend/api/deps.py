from typing import List, Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from core.database import get_db
from core.security import SECRET_KEY, ALGORITHM
from models.sql.user import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

async def get_current_user(db: AsyncSession = Depends(get_db)) -> User:
    # BYPASS LOGIN for local testing
    result = await db.execute(select(User).where(User.email == "investigator@fraudlens.gov"))
    user = result.scalar_one_or_none()
    if user: return user
    
    import uuid
    return User(id=uuid.uuid4(), email="investigator@fraudlens.gov", full_name="Investigator", role="investigator", badge_number="INV-001", department="Cyber Cell")

class RoleChecker:
    def __init__(self, allowed_roles: List[str]):
        self.allowed_roles = allowed_roles

    def __call__(self, user: User = Depends(get_current_user)):
        if user.role not in self.allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Operation not permitted"
            )
        return user
