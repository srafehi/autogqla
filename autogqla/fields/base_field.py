import traceback
from typing import Generic
from typing import TypeVar

from autogqla.spec_resolver import ModelSpecResolver

T = TypeVar('T')


class BaseField(Generic[T]):

    def __init__(self, session_func, resolver: ModelSpecResolver, spec: T, arguments: dict = None):
        self.session_func = session_func
        self.resolver = resolver
        self.spec: T = spec
        self._field = None
        self.arguments = arguments or {}

    @property
    def name(self):
        return self._name()

    @property
    def field(self):
        if self._field is None:
            self._field = self._make_field()
        return self._field

    def _name(self) -> str:
        raise NotImplementedError

    def _make_field(self):
        raise NotImplementedError

    def execute(self, instance, info, **arguments):
        try:
            return self._execute(instance, info, **arguments)
        except Exception:
            traceback.print_exc()
            raise

    def _execute(self, instance, info, **arguments):
        raise NotImplementedError

    def __call__(self, *args, **kwargs):
        return self._execute(*args, **kwargs)
