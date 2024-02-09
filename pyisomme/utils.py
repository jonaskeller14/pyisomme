import logging


intend = "\t"


def debug_logging(func):
    def wrapper(*args, **kwargs):
        global intend

        args_repr = [repr(arg) for arg in args]
        kwargs_repr = [f"{key}={value!r}" for key, value in kwargs.items()]
        signature = ", ".join(args_repr + kwargs_repr)
        logging.debug(f"{intend}{func.__name__}({signature})")

        intend += "\t"
        result = func(*args, **kwargs)
        intend = intend[:-1]

        logging.debug(f"{intend}--> {result!r}")

        return result
    return wrapper
