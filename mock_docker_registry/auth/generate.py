from datetime import datetime, timedelta
from typing import Optional, List, Union

from jose import jwt

from multimethod import multimethod
from pydantic.datetime_parse import parse_datetime

from mock_docker_registry.config.auth import (
    ALGORITHM,
    AUDIENCE,
    DEFAULT_TOKEN_VALIDITY_PERIOD,
    ISSUER,
    SECRET_KEY,
)
from mock_docker_registry.models.auth import TokenData

__all__ = ["create_token"]


def now_plus(delta: timedelta):
    return datetime.utcnow() + delta


def create_jwt(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta is None:
        expires_delta = DEFAULT_TOKEN_VALIDITY_PERIOD
    if "exp" not in to_encode:
        to_encode.update({"exp": now_plus(expires_delta)})
    encoded_token = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_token


@multimethod
def create_token(
    subject: str,
    access: List[dict],
    expiration: Union[None, datetime, timedelta, str, int] = None,
):
    if expiration is None:
        expiration = now_plus(DEFAULT_TOKEN_VALIDITY_PERIOD)
    elif isinstance(expiration, int):
        if expiration < (60 * 60 * 24 * 365):
            expiration = now_plus(timedelta(seconds=expiration))
        else:
            expiration = datetime.fromtimestamp(expiration)
    elif isinstance(expiration, timedelta):
        expiration = now_plus(expiration)
    elif isinstance(expiration, str):
        expiration = parse_datetime(expiration)
    token_data = TokenData(
        subject=subject,
        access=access,
        issuer=ISSUER,
        audience=AUDIENCE,
        expiration=expiration,
        issued=datetime.utcnow(),
    )
    return create_token(token_data=token_data)


@multimethod
def create_token(
    token_data: TokenData,
):
    not_before = token_data.issued - timedelta(seconds=5)
    data = {
        "iss": token_data.issuer,
        "sub": token_data.subject,
        "aud": token_data.audience,
        "exp": int(token_data.expiration.timestamp()),
        "iat": int(token_data.issued.timestamp()),
        "nbf": int(not_before.timestamp()),
        "access": [scope.dict() for scope in token_data.access],
    }

    return create_jwt(data)
