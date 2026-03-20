from datetime import datetime, timedelta

from jose import jwt

SECRET_KEY = '25bba350704372dace494e057a20d11e8e56d9d62cf300ebead37d28014c2519'


def create_access_token(driver_id: str) -> str:
    payload = {'sub': driver_id, 'exp': datetime.now() + timedelta(hours=1)}
    return jwt.encode(payload, SECRET_KEY, algorithm='HS256')


def decode_token(token: str) -> int:
    payload = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
    return payload['sub']
