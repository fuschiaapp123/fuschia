from passlib.context import CryptContext
import hashlib

# Use only pbkdf2_sha256 to avoid bcrypt 72-byte limit issues
pwd_context = CryptContext(
    schemes=["pbkdf2_sha256", "bcrypt"],
    deprecated=["bcrypt"],
    pbkdf2_sha256__default_rounds=29000
)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    # Handle bcrypt's 72-byte limit for passwords
    if len(plain_password.encode('utf-8')) > 72:
        plain_password = plain_password[:72]
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    # Bcrypt has a 72-byte limit for passwords
    if len(password.encode('utf-8')) > 72:
        password = password[:72]
    return pwd_context.hash(password)