import uuid
from sqlalchemy.orm import Session
from passlib.context import CryptContext

from app.db.models import User

pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
)


def create_user_id() -> str:
    return f"user_{uuid.uuid4().hex[:12]}"


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    return pwd_context.verify(password, password_hash)


def signup_user(
    db: Session,
    email: str,
    password: str,
    name: str | None = None,
) -> User:
    existing = db.query(User).filter(User.email == email).first()

    if existing:
        raise ValueError("Email already registered.")

    user = User(
        user_id=create_user_id(),
        email=email,
        name=name,
        password_hash=hash_password(password),
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    return user


def login_user(
    db: Session,
    email: str,
    password: str,
) -> User:
    user = db.query(User).filter(User.email == email).first()

    if not user:
        raise ValueError("Invalid email or password.")

    if not verify_password(password, user.password_hash):
        raise ValueError("Invalid email or password.")

    return user