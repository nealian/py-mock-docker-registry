from datetime import datetime
from enum import Enum

from mock_docker_registry.models.model import BaseEntity
from typing import List


class ResourceType(str, Enum):
    REGISTRY = "registry"
    REPOSITORY = "repository"


class ResourceAction(str, Enum):
    PUSH = "push"
    PULL = "pull"
    LIST = "list"


class Token(BaseEntity):
    access_token: str
    token_type: str


class TokenAccess(BaseEntity):
    type: ResourceType
    name: str
    actions: List[ResourceAction]


class TokenData(BaseEntity):
    access: List[TokenAccess]
    subject: str
    issuer: str
    audience: str
    expiration: datetime
    issued: datetime
