"""Create admin user on server: phone=13800000000, password=admin123"""
import sys
sys.path.insert(0, '/opt/hxmall')

from app.database import async_session_factory
from app.models.user import User, UserRole, UserStatus, RetailerLevel
from app.services.auth_service import hash_password
from sqlalchemy import select
import asyncio


async def create_admin():
    async with async_session_factory() as session:
        # Check if admin already exists
        result = await session.execute(
            select(User).where(User.phone == "13800000000")
        )
        existing = result.scalar_one_or_none()
        if existing:
            print(f"Admin already exists: id={existing.id}, phone={existing.phone}, role={existing.role}")
            return

        # Create admin user
        admin = User(
            phone="13800000000",
            hashed_password=hash_password("admin123"),
            role=UserRole.ADMIN,
            level=RetailerLevel.NORMAL,
            status=UserStatus.ACTIVE,
        )
        session.add(admin)
        await session.commit()
        await session.refresh(admin)
        print(f"Admin created successfully!")
        print(f"  ID: {admin.id}")
        print(f"  Phone: {admin.phone}")
        print(f"  Role: {admin.role.value}")
        print(f"  Status: {admin.status.value}")


if __name__ == "__main__":
    asyncio.run(create_admin())
