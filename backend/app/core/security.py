from datetime import datetime, timedelta, timezone

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import get_settings
from app.core.exceptions import BusinessException

# Use PBKDF2 for broad runtime compatibility (Python 3.8 friendly).
pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")


def verify_password(plain_password: str, password_hash: str) -> bool:
    try:
        return pwd_context.verify(plain_password, password_hash)
    except Exception:
        return False


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def create_token(subject: str, token_type: str = "access") -> str:
    settings = get_settings()
    delta_minutes = (
        settings.access_token_expire_minutes if token_type == "access" else settings.refresh_token_expire_minutes
    )
    expire = datetime.now(timezone.utc) + timedelta(minutes=delta_minutes)
    payload = {"sub": subject, "exp": expire, "token_type": token_type}
    return jwt.encode(payload, settings.secret_key, algorithm=settings.jwt_algorithm)


def decode_token(token: str) -> dict:
    settings = get_settings()
    try:
        return jwt.decode(token, settings.secret_key, algorithms=[settings.jwt_algorithm])
    except JWTError as exc:
        raise BusinessException(code=4010, message="invalid token") from exc
