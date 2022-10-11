from typing import Optional, List
from typing_extensions import Literal

from pydantic.dataclasses import dataclass
from pydantic.networks import AnyUrl
from pydantic.fields import Field

from mock_docker_registry.models.repository import Digest
from mock_docker_registry.models.model import BaseEntity


class Manifest(BaseEntity):
    @dataclass(frozen=True)
    class ConfigReference:
        mediaType: Literal['application/vnd.docker.container.image.v1+json']
        size: int
        digest: Digest

    @dataclass(frozen=True)
    class LayerReference:
        mediaType: Literal['application/vnd.docker.image.rootfs.diff.tar.gzip',
                           'application/vnd.docker.image.rootfs.foreign.diff.tar.gzip']
        size: int
        digest: Digest
        urls: Optional[List[AnyUrl]] = None

    schemaVersion: Literal[2] = 2
    mediaType: Literal['application/vnd.docker.distribution.manifest.v2+json'] = \
        'application/vnd.docker.distribution.manifest.v2+json'
    config: ConfigReference
    layers: List[LayerReference]


class ManifestList(BaseEntity):
    @dataclass(frozen=True)
    class ManifestReference:
        class PlatformReferenceConfig:
            allow_population_by_field_name = True

        @dataclass(frozen=True, config=PlatformReferenceConfig)
        class PlatformReference:
            # From https://go.dev/doc/install/source#environment
            architecture: Literal[
                'ppc64',
                '386',
                'amd64',
                'arm',
                'arm64',
                'wasm',
                'loong64',
                'mips',
                'mipsle',
                'mips64',
                'mips64le',
                'ppc64le',
                'riscv64',
                's390x',
            ]
            # Also from https://go.dev/doc/install/source#environment
            os: Literal[
                'aix',
                'android',
                'darwin',
                'dragonfly',
                'freebsd',
                'illumos',
                'ios',
                'js',
                'linux',
                'netbsd',
                'openbsd',
                'plan9',
                'solaris',
                'windows'
            ]
            os_version: Optional[str] = Field(default=None, alias='os.version')
            os_features: Optional[List[str]] = Field(default=None, alias='os.features')
            variant: Optional[str] = None
            features: Optional[List[str]] = None

        mediaType: Literal['application/vnd.docker.distribution.manifest.v2+json']
        size: int
        digest: Digest
        platform: PlatformReference

    schemaVersion: Literal[2] = 2
    mediaType: Literal['application/vnd.docker.distribution.manifest.list.v2+json'] = \
        'application/vnd.docker.distribution.manifest.list.v2+json'
    manifests: List[ManifestReference]
