from pydantic import BaseModel
from enum import StrEnum
from typing import Any, List, Optional, Type


class ErrorCode(StrEnum):
    BLOB_UNKNOWN = 'BLOB_UNKNOWN'
    BLOB_UPLOAD_INVALID = 'BLOB_UPLOAD_INVALID'
    BLOB_UPLOAD_UNKNOWN = 'BLOB_UPLOAD_UNKNOWN'
    DIGEST_INVALID = 'DIGEST_INVALID'
    MANIFEST_BLOB_UNKNOWN = 'MANIFEST_BLOB_UNKNOWN'
    MANIFEST_INVALID = 'MANIFEST_INVALID'
    MANIFEST_UNKNOWN = 'MANIFEST_UNKNOWN'
    MANIFEST_UNVERIFIED = 'MANIFEST_UNVERIFIED'
    NAME_INVALID = 'NAME_INVALID'
    NAME_UNKNOWN = 'NAME_UNKNOWN'
    SIZE_INVALID = 'SIZE_INVALID'
    TAG_INVALID = 'TAG_INVALID'
    UNAUTHORIZED = 'UNAUTHORIZED'
    DENIED = 'DENIED'
    UNSUPPORTED = 'UNSUPPORTED'
    TOOMANYREQUESTS = 'TOOMANYREQUESTS' # noqa


class ErrorMessage(StrEnum):
    """
    A mapping of Docker Registry v2 error codes to their respective messages.
    """
    BLOB_UNKNOWN = 'blob unknown to registry'
    BLOB_UPLOAD_INVALID = 'blob upload invalid'
    BLOB_UPLOAD_UNKNOWN = 'blob upload unknown to registry'
    DIGEST_INVALID = 'provided digest did not match uploaded content'
    MANIFEST_BLOB_UNKNOWN = 'blob unknown to registry'
    MANIFEST_INVALID = 'manifest invalid'
    MANIFEST_UNKNOWN = 'manifest unknown'
    MANIFEST_UNVERIFIED = 'manifest failed signature verification'
    NAME_INVALID = 'invalid repository name'
    NAME_UNKNOWN = 'repository name not known to registry'
    SIZE_INVALID = 'provided length did not match content length'
    TAG_INVALID = 'manifest tag did not match URI'
    UNAUTHORIZED = 'authentication required'
    DENIED = 'requested access to the resource is denied'
    UNSUPPORTED = 'The operation is unsupported'
    TOOMANYREQUESTS = 'too many requests' # noqa


class Error(BaseModel):
    code: ErrorCode
    message: ErrorMessage
    detail: Any


class ErrorList(BaseModel):
    errors: List[Error]


class ExceptionMapping(Exception):
    def __init__(
            self,
            code: ErrorCode | str,
            type: Type[Exception],
            detail: Optional[Any] = None,
    ):
        if not isinstance(code, ErrorCode):
            if code not in list(ErrorCode):
                raise ValueError('code must be a valid registry error code (ErrorCode)')
        self.code = code.value
        self.message = ErrorMessage[code.value] # noqa # PyCharm thinks value is, and must be, callable.
        self.detail = detail
        self._exception = type

    def __call__(self, *args):
        raise self._exception(*args)
