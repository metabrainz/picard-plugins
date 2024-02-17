from contextlib import contextmanager
from typing import Generator


@contextmanager
def override_module(object: object) -> Generator[None, None, None]:
    # picard expects hooks to be defined at module level
    module = object.__module__
    object.__module__ = ".".join(module.split(".")[:-1])
    yield
    object.__module__ = module
