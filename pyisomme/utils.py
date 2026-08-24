import logging
import math
from typing import Any, Callable, TypeVar, overload

import numpy as np

intend = "\t"

F = TypeVar("F", bound=Callable[..., object])


@overload
def debug_logging(logger_or_func: logging.Logger) -> Callable[[F], F]: ...
@overload
def debug_logging(logger_or_func: F) -> F: ...
def debug_logging(logger_or_func):
    def decorator(func):
        def wrapper(*args, **kwargs):
            global intend

            logger = (
                logging.getLogger(__name__)
                if callable(logger_or_func)
                else logger_or_func
            )

            args_repr = [repr(arg) for arg in args]
            kwargs_repr = [f"{key}={value!r}" for key, value in kwargs.items()]
            signature = ", ".join(args_repr + kwargs_repr)
            logger.debug(f"{intend}{func.__name__}({signature})")

            intend += "\t"
            result = func(*args, **kwargs)
            intend = intend[:-1]

            logger.debug(f"{intend}--> {result!r}")

            return result

        return wrapper

    return decorator(logger_or_func) if callable(logger_or_func) else decorator


def json_encode(value: Any) -> Any:
    """Make a criterion/limit scalar JSON-safe without losing nan/inf identity."""
    # TODO: add tests
    if isinstance(value, np.generic):
        value = value.item()
    if isinstance(value, bool) or value is None or isinstance(value, (int, str)):
        return value
    if isinstance(value, float):
        if math.isnan(value):
            return "nan"
        if math.isinf(value):
            return "inf" if value > 0 else "-inf"
        return value
    if isinstance(value, (tuple, list, np.ndarray)):
        return [json_encode(item) for item in value]
    return repr(value)


def json_decode(value: Any) -> Any:
    """Inverse of :func:`encode` for the three special float spellings."""
    # TODO: add tests
    if value == "nan":
        return float("nan")
    if value == "inf":
        return float("inf")
    if value == "-inf":
        return float("-inf")
    return value
