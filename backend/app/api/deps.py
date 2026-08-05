from uuid import UUID
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from jose import JWTError, jwt
from app.config import get_settings
from app.database import get_db
from app.redis import get_redis

security = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Verify JWT token and return user payload. Raises 401 if invalid."""
    if credentials is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="请先登录")
    settings = get_settings()
    try:
        payload = jwt.decode(
            credentials.credentials, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM]
        )
        user_id: str = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token无效")
        return {"user_id": UUID(user_id), "role": payload.get("role", "retailer")}
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token无效或已过期")


async def get_current_admin(current_user: dict = Depends(get_current_user)) -> dict:
    """Require admin role. Raises 403 if not admin."""
    if current_user["role"] not in ("admin", "operator"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="需要管理员权限")
    return current_user


def require_role(*roles: str):
    """Factory: create a dependency that requires one of the given roles."""

    async def _check(current_user: dict = Depends(get_current_user)) -> dict:
        if current_user["role"] not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail=f"需要{'/'.join(roles)}权限"
            )
        return current_user

    return _check
