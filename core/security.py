from jose import jwt
from core.config import settings

def decode_token(token: str):
    return jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])