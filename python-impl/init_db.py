import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from db.database import engine, Base
from db.models import User
from db.database import SessionLocal
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def create_tables():
    Base.metadata.create_all(bind=engine)
    print("✅ 表创建成功")


def create_admin_user():
    db = SessionLocal()
    try:
        existing_user = db.query(User).filter(User.username == "admin").first()
        if existing_user:
            print("⚠️ admin 用户已存在，跳过创建")
            return

        hashed_password = pwd_context.hash("admin123")
        admin_user = User(
            username="admin",
            password_hash=hashed_password,
            role="管理员"
        )
        db.add(admin_user)
        db.commit()
        db.refresh(admin_user)
        print("✅ 管理员用户创建成功")
        print(f"   用户名: admin")
        print(f"   密码: admin123")
        print(f"   角色: 管理员")
    except Exception as e:
        print(f"❌ 创建用户失败: {e}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    print("🚀 开始初始化数据库...")
    create_tables()
    create_admin_user()
    print("🎉 数据库初始化完成")
