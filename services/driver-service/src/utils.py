import os
from datetime import datetime, timedelta

from jose import jwt

SECRET_KEY = os.environ.get('JWT_SECRET_KEY', 'super-secret-key-change-in-prod')


def create_access_token(driver_id: str) -> str:
    payload = {'sub': driver_id, 'exp': datetime.now() + timedelta(hours=24)}
    return jwt.encode(payload, SECRET_KEY, algorithm='HS256')


def decode_token(token: str) -> str:
    payload = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
    return payload['sub']
