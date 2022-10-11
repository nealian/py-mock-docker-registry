from pydantic import BaseModel
from typing_extensions import Type, Protocol
from typing import Iterator, TypeVar, Callable, Generic, List, Union
from functools import reduce

__all__ = ["BaseEntity", "ValidatedValue"]


# Spooky. Shamelessly pulled directly from https://github.com/pydantic/pydantic/issues/935#issuecomment-1202998566
class BaseEntity(BaseModel):
    """
    Wrapper around pydantic.BaseModel that allows properties to be first-class citizens.
    """

    # Workaround for serializing properties with pydantic until
    # https://github.com/samuelcolvin/pydantic/issues/935
    # is solved
    @classmethod
    def get_properties(cls):
        return [prop for prop in dir(cls) if isinstance(getattr(cls, prop), property)]

    def dict(self, *args, **kwargs):
        self.__dict__.update(
            {prop: getattr(self, prop) for prop in self.get_properties()}
        )
        return super().dict(*args, **kwargs)

    def json(
        self,
        *args,
        **kwargs,
    ) -> str:
        self.__dict__.update(
            {prop: getattr(self, prop) for prop in self.get_properties()}
        )

        return super().json(*args, **kwargs)


# Turns out, also kinda spooky. Shamelessly pulled directly from
# https://www.madelyneriksen.com/blog/validated-container-types-python-pydantic
T = TypeVar("T")
Validator = Callable[[T], T]


class ValidatedType(Protocol[T]):
    """Any type that implements __get_validators__.
    Shamelessly taken from https://www.madelyneriksen.com/blog/validated-container-types-python-pydantic
    """

    @classmethod
    def __get_validators__(cls) -> Iterator[Validator[T]]:
        """Retrieve validators for this item."""
        ...

    @staticmethod
    def validate(
        validated_type: Type["ValidatedType[T]"],
        *args,
        **kwargs,
    ):
        raise NotImplementedError


class ValidatedValue(Generic[T]):
    """A container for a validated value of some type.
    Shamelessly taken from https://www.madelyneriksen.com/blog/validated-container-types-python-pydantic
    """

    __validators__: List[Validator[T]]

    @classmethod
    def __get_validators__(cls) -> Iterator[Validator[T]]:
        yield from cls.__validators__

    @staticmethod
    def validate(
        validated_type: Type[ValidatedType[T]],
        value: T,
    ) -> T:
        """Validate the value against Pydantic __get_validators__ method."""

        def _do_validation(func_: Validator, value_: T) -> T:
            return func_(value_)

        return reduce(_do_validation, validated_type.__get_validators__(), value)

    def __init__(
        self,
        value: Union[T, "ValidatedValue[T]"],
    ) -> None:
        if isinstance(value, type(self)):
            self._value: T = value._value
        else:
            self._value: T = self.validate(validated_type=type(self), value=value)
