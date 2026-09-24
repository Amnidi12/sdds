import asyncio
from sqlalchemy import text
from app.core.security import hash_password
from app.db.session import AsyncSessionLocal
from app.users.models import RoleName, User
from app.organizations.models import Organization

async def seed() -> None:
    async with AsyncSessionLocal() as db:
        # Clear all existing tables safely
        print("Clearing database...")
        await db.execute(text("TRUNCATE TABLE organizations CASCADE"))
        await db.execute(text("TRUNCATE TABLE users CASCADE"))
        # Create superadmin
        print("Creating superadmin...")
        user = User(
            email="admin@gmail.com",
            password_hash=hash_password("admin123"),
            full_name="Super Admin",
            role=RoleName.SUPER_ADMIN,
            is_active=True,
            is_email_verified=True,
        )
        db.add(user)
        await db.commit()
        print("\nDatabase cleared and superadmin created.")
        print("Username: admin")
        print("Password: admin123")

if __name__ == "__main__":
    asyncio.run(seed())
