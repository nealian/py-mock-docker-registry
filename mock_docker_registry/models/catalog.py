from typing import List

from mock_docker_registry.models.model import BaseEntity, ValidatedValue


class Catalog(BaseEntity):
    repositories: List[str]
