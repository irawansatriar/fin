# file: auth.py
from passlib.context import CryptContext
from models import SessionLocal, User
from sqlalchemy.exc import IntegrityError

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(password: str, hashed: str) -> bool:
    return pwd_context.verify(password, hashed)

def create_user(email: str, password: str):
    db = SessionLocal()
    user = User(email=email, password_hash=hash_password(password))
    db.add(user)
    try:
        db.commit()
        db.refresh(user)
    except IntegrityError:
        db.rollback()
        db.close()
        raise ValueError("User already exists")
    db.close()
    return user

def authenticate(email: str, password: str):
    db = SessionLocal()
    user = db.query(User).filter(User.email == email).first()
    db.close()
    if not user:
        return None
    if verify_password(password, user.password_hash):
        return user
    return None