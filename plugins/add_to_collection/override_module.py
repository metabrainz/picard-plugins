from contextlib import contextmanager
from typing import Generator


@contextmanager
def override_module(obj: object) -> Generator[None, None, None]:
    # picard expects hooks to be defined at module level
    module = obj.__module__
    obj.__module__ = ".".join(module.split(".")[:-1])
    yield
    obj.__module__ = module
