import logging


intend = "\t"


def debug_logging(name_or_func):
    def decorator(func):
        def wrapper(*args, **kwargs):
            global intend

            logger = logging.getLogger(name_or_func if not callable(name_or_func) else __name__)

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
    return decorator(name_or_func) if callable(name_or_func) else decorator
