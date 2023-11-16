import hashlib
import re
from string import hexdigits
from typing import AnyStr, Dict, Tuple, Set, List, Union, Optional

from mock_docker_registry.models.model import BaseEntity, ValidatedValue
from mock_docker_registry.models.repository.ManifestV2Schema2 import (
    Manifest,
    ManifestList,
)
from mock_docker_registry.utils.error_utils import (
    mutually_exclusive,
    one_required,
)


class Digest(ValidatedValue[str]):
    """Must look like 'sha256:0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef'."""  # noqa

    valid_algorithms: Set[str] = {
        "sha256",
    }
    available_algorithms: Set[str] = valid_algorithms.union(
        hashlib.algorithms_available
    )
    hash_lengths: Dict[str, int] = {
        "sha256": 64,
    }
    valid_prefixes: tuple = tuple([f"{algo}:" for algo in list(available_algorithms)])

    @classmethod
    def _pop_prefix(
        cls,
        value: str,
    ) -> Tuple[str, str]:
        _val = value
        _pfx = None
        for prefix in cls.valid_prefixes:
            if _val.startswith(prefix):
                _pfx = prefix
                _val = _val.removeprefix(_pfx)
                break
        return _pfx, _val

    @classmethod
    def is_prefixed(cls, value: str) -> str:
        _val = str(value)
        if not _val.startswith(cls.valid_prefixes):
            raise ValueError(f"digest must begin with one of {cls.valid_algorithms}")
        return _val

    @classmethod
    def is_hex(cls, value: str) -> str:
        _val = str(value)
        _, _hex = cls._pop_prefix(value=_val)
        if not all(c in hexdigits for c in _hex):
            raise ValueError("digest must be hexadecimal")
        return _val

    @classmethod
    def is_correct_length(
        cls,
        value: str,
    ) -> str:
        _val = str(value)
        _pfx, _hex = cls._pop_prefix(value=value)
        if len(_hex) != cls.hash_lengths[_pfx]:
            raise ValueError("digest must be of correct length")
        return _val

    __validators__ = [is_prefixed, is_hex, is_correct_length]

    def __str__(self):
        return str(self._value).lower()

    def __bytes__(self):
        _, _hex = self._pop_prefix(str(self))
        return bytes.fromhex(_hex)

    @classmethod
    def from_hex(
        cls, hex_digits: str, algorithm: available_algorithms = "sha256"
    ) -> "Digest":
        return cls(f"{algorithm}:{hex_digits}")


class DockerImageReferenceParts:
    """Based mostly on https://github.com/distribution/distribution/blob/main/reference/regexp.go
    Note that the patterns for host name and for digest are *much* more generous than the RFCs and the actual used
    digest algorithms.
    Public attributes are compiled patterns with named capture groups for components as necessary.
    Private attributes are raw "verbose" patterns to show the logic.

    The names "repo", "registry", and "image" are used very intentionally here; a "registry" refers to a host specifier
    only, a "repo" refers to the "name" for an image (also optionally including the registry), and an "image" refers
    to a repo and optional tag and/or optional digest designator. All together, this looks like:
        <repo> = <registry>/<name>
        <image> = <repo>[:<tag>][@<digest>]
    or for a concrete example, for a particular image for a beautiful documentation renderer
        registry = ghcr.io
        name = docat-org/docat
        tag = 0.2.3
        digest = sha256:6aeda7739383a56fb2240eee04ab4a9cc4b3d1028c24db2f09ad50e8f42a92aa
        repo = ghcr.io/docat-org/docat
        image is one of
          ghcr.io/docat-org/docat:0.2.3
        or
          ghcr.io/docat-org/docat@sha256:6aeda7739383a56fb2240eee04ab4a9cc4b3d1028c24db2f09ad50e8f42a92aa
    """ # noqa

    _host_name_pattern_raw = r"""
    (?:             # Non-capture group to break up subcomponents
      [a-zA-Z0-9]   # No hyphens as first character
      [a-zA-Z0-9-]* # Hyphens allowed in the middle
      [a-zA-Z0-9]   # No hyphens at the end
      |[a-zA-Z0-9]  # Technically a single alphanumeric is allowed as a host name component
    )               # First component in a hostname is required, FQDN is not required
    (?:             # Another non-capture group to specify optional further components
      [.]           # Literal dots separate components / subdomains
      (?:           # The rest of the additional components must look like the first; explanation will not be repeated
        [a-zA-Z0-9][a-zA-Z0-9-]*[a-zA-Z0-9]|[a-zA-Z0-9]
      )
    )*              # 0 or more components after the first
    # This pattern also happens to capture IPv4 addresses as well, so they don't need to be handled separately. Yay
    """

    _ipv6_pattern_raw = r"""
    (?:             # Non-capture group to wrap it all up in
      \[            # Must start with literal [
      [a-fA-F0-9:]+ # Hex components separated by colons; we're not too picky about the details here
      \]            # Must end with literal ]
    )
    """

    _registry_pattern_raw = (
        r"""
        (?P<host>       # Named capture group for the host
        """
        + _host_name_pattern_raw
        + r"""
          |             # Also let's allow IPv6
          """
        + _ipv6_pattern_raw
        + r"""
          )               # End name component
          (?:             # Begin non-capture group for optional port
            [:]           # Port separator, literal :
            (?P<port>     # Named capture group for port number
              [0-9]+
            )
          )?
          """
    )

    _repo_name_pattern_raw = r"""
    (?P<name>       # Named capture group for the image path
      (?:           # We start at the root path
        [a-z0-9]+   # Must start with one or more lowercase alphanumeric characters
        (?:         # Middle characters are treated differently...
          (?:       # This is where it gets weird:
            [._]|   # - One dot or underscore, or
            __|     # - Two underscores, or
            [-]*    # - Any number of dashes
          )         # are allowed to be in the middle
          [a-z0-9]+ # but must be trailed by one or more lowercase alphanumeric characters
        )*          # Any number of sets of these alphanumerics and "separators" are allowed.
      )             # We must have at least one "name component"
      (?:           # But we can have more, separated by slashes (but we can skip explaining it again)
        [/][a-z0-9]+(?:(?:[._]|__|[-]*)[a-z0-9]+)*
      )*
    )
    """

    _tag_pattern_raw = r"""
    (?P<tag>        # The tag is pretty simple
      [\w]          # Start with a "word" character; in ascii, that's alphanumeric, both cases, plus underscore
      [\w.-]{0,127} # Allow up to 127 more characters, which may be "word" characters, periods, or hyphens.
    )
    """

    _digest_pattern_raw = r"""
    (?P<digest>     # The digest is a bit more complicated than the tag...
      [A-Za-z]      # Must start with a letter
      [A-Za-z0-9]*  # Non-separators must be alphanumeric
      (?:           # We do allow some separators
        [-_+.]      # Specifically, these four characters
        [A-Za-z]    # Which must again be followed by a letter
        [A-Za-z0-9]* # And again allow more alphanumerics
      )*
      [:]           # Then there must be a literal :
      [A-Fa-f0-9]{32,} # then at least 32 hexadecimal digits
    )
    """

    _repo_pattern_raw = (
        r"(?:" + _registry_pattern_raw + r"[/])?" + _repo_name_pattern_raw
    )
    _image_pattern_raw = (
        _repo_pattern_raw
        + r"(?:[:]"
        + _tag_pattern_raw
        + r"""
          )?
          (?:
            (?(tag)       # Check if tag has matched
              $           # If so, this must be the end
              |[@]        # If not, continue
          """
        + _digest_pattern_raw
        + r"))?"
    )

    host_name_pattern = re.compile(_host_name_pattern_raw, re.VERBOSE)
    ipv6_pattern = re.compile(_ipv6_pattern_raw, re.VERBOSE)
    registry_pattern = re.compile(_registry_pattern_raw, re.VERBOSE)
    repo_name_pattern = re.compile(_repo_name_pattern_raw, re.VERBOSE)
    tag_pattern = re.compile(_tag_pattern_raw, re.VERBOSE)
    digest_pattern = re.compile(_digest_pattern_raw, re.VERBOSE)
    repo_pattern = re.compile(_repo_pattern_raw, re.VERBOSE)
    image_pattern = re.compile(_image_pattern_raw, re.VERBOSE)

    __new__ = None
    __init__ = None


class DockerImageReference:
    host: Optional[str] = None
    port: int = 443
    name: str
    tag: Optional[str] = None
    digest: Optional[str] = None

    def __init__(
        self,
        image_str: Optional[str] = None,
        *,
        host: Optional[str] = None,
        port: Union[None, str, int] = None,
        name: Optional[str] = None,
        tag: Optional[str] = None,
        digest: Optional[str] = None,
    ):
        mutually_exclusive(tag=tag, digest=digest)
        one_required(image_str=image_str, name=name)

        if image_str is not None:
            self._image = image_str
        if host is not None:
            self.host = host
        if isinstance(port, str):
            self.port = int(port)
        elif isinstance(port, int):
            self.port = port
        if name is not None:
            self.name = name
        if tag is not None:
            self.tag = tag
        if digest is not None:
            self.digest = digest

    @property
    def _image(self) -> str:
        image = self.name
        if self.host is not None:
            host = self.host
            if self.port != 443:
                host = f"{host}:{self.port}"
            image = f"{host}/{image}"
        if self.tag is not None:
            image = f"{image}:{self.tag}"
        elif self.digest is not None:
            image = f"{image}@{self.digest}"
        return image

    @_image.setter
    def _image(
        self,
        image: str,
    ):
        match = DockerImageReferenceParts.image_pattern.match(image)
        match_dict = {k: v for k, v in match.groupdict().items()}
        match_dict['port'] = 443 if match_dict['port'] is None else match_dict['port']
        self.__dict__.update(match_dict)

    def __str__(self):
        return self._image

    def __repr__(self):
        return f"DockerImageReference('{str(self)}')"


class Blob(BaseEntity):
    data: AnyStr
    digest_algorithm: Digest.available_algorithms = "sha256"

    @property
    def digest(self) -> Digest:
        _data = self.data
        if isinstance(self.data, str):
            _data = _data.encode("utf-8")
        _hex = hashlib.new(name=self.digest_algorithm, data=_data).hexdigest()
        _digest = Digest.from_hex(hex_digits=_hex, algorithm=self.digest_algorithm)
        return _digest

    @property
    def size(self) -> int:
        return len(self.data)


class Tags(BaseEntity):
    tags: List[str]
