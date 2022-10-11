from typing import Optional, Union, Tuple, List

from jose import jwt, ExpiredSignatureError
from multimethod import multimethod

from mock_docker_registry.config.auth import ALGORITHM, AUDIENCE, ISSUER, SECRET_KEY
from mock_docker_registry.models.auth import ResourceType, ResourceAction

__all__ = ["validate_token_data"]


def get_token_data(encoded_token: str) -> Optional[dict]:
    try:
        token_data = jwt.decode(
            encoded_token,
            SECRET_KEY,
            algorithms=[ALGORITHM],
            audience=AUDIENCE,
            issuer=ISSUER,
        )
    except ExpiredSignatureError:
        return None
    return token_data


ThrupleStr = Tuple[str, str, str]
ThrupleStrL = List[ThrupleStr]
ThrupleStrU = Union[ThrupleStr, ThrupleStrL]


@multimethod
def scope_is_allowed(scope: ThrupleStr, access: List[dict]):
    type_, name, action = scope
    for access_scope in access:
        if access_scope["type"] == type_:
            if access_scope["name"] == name:
                if action in access_scope["actions"]:
                    return True
    return False


@multimethod
def scope_is_allowed(scope: ThrupleStrL, access: List[dict]):
    for scope_ in scope:
        if not scope_is_allowed(scope_, access):
            return False
    return True


@multimethod
def validate_token_data(data: dict) -> Optional[dict]:
    # We assume that jose.decode has already validated issuer, audience, expiration, and issued_at.
    # Just validate 'access', then
    try:
        assert isinstance(access := data["access"], list)
        for scope in access:
            assert isinstance(scope, dict)
            assert isinstance(type_ := scope["type"], str)
            assert type_ in list(ResourceType)
            assert isinstance(scope["name"], str)
            assert isinstance(actions := scope["actions"], list)
            for action in actions:
                assert isinstance(action, str)
                assert action in list(ResourceAction)
    except (AssertionError, KeyError):
        return None
    return data


@multimethod
def validate_token_data(data: str) -> Optional[dict]:
    data = get_token_data(data)
    if data is None:
        return None
    return validate_token_data(data=data)


@multimethod
def validate_token_data(data: Union[str, dict], scope: ThrupleStrU) -> Optional[dict]:
    data = validate_token_data(data)
    if data is None:
        return None
    return data if scope_is_allowed(scope, data["access"]) else None


@multimethod
def validate_token_data(data: Union[str, dict], scope: str) -> Optional[dict]:
    scopes = []
    for scope_ in scope.split(" "):
        scope_parts = scope_.split(":")
        if len(scope_parts) < 3:
            raise ValueError(f"Scope string is invalid: {scope_}")
        type_ = scope_parts[0]
        name = ":".join(scope_parts[1:-1])
        action = scope_parts[-1]
        scopes.append((type_, name, action))
    return validate_token_data(data=data, scope=scopes)
