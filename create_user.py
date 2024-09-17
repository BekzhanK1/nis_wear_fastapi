from sqlalchemy.orm import Session
from database import SessionLocal
from models import User
from auth import get_password_hash

db = SessionLocal()


def create_user(username: str, password: str):
    # Check if user already exists
    existing_user = db.query(User).filter(User.username == username).first()
    if existing_user:
        print(f"User with username {username} already exists.")
        return

    user = User(username=username, hashed_password=get_password_hash(password))
    db.add(user)
    db.commit()
    db.refresh(user)
    print(f"User {username} created successfully.")


if __name__ == "__main__":
    username = input("Enter username: ")
    password = input("Enter password: ")
    create_user(username, password)
