def qual_type(obj: object) -> str:
    cls = type(obj)
    mod = cls.__module__
    name = cls.__qualname__
    if mod is not None and mod != "__builtin__":
        name = f"{mod}.{name}"
    return name


def mutually_exclusive(
    missing_sentinel=None,
    **kwargs,
) -> None:
    if len(kwargs) > 1:
        not_missing = [k for k, v in kwargs.items() if v is not missing_sentinel]
        if len(not_missing) > 1:
            raise ValueError(
                f"More than one mutually exclusive parameter (of {sorted(kwargs.keys())}) was defined: {not_missing}"
            )


def all_required(
    missing_sentinel=None,
    **kwargs,
) -> None:
    missing = [k for k, v in kwargs.items() if v is missing_sentinel]
    if len(missing) > 0:
        raise ValueError(
            f"The following required parameter(s) have not been set: {missing}"
        )


def one_required(
    missing_sentinel=None,
    **kwargs,
) -> None:
    not_missing = [k for k, v in kwargs.items() if v is not missing_sentinel]
    if len(not_missing) < 1:
        raise ValueError(
            f"One of the following parameter(s) is required: {sorted(kwargs.keys())}"
        )
