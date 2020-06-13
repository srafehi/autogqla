import base64
import json
from typing import Tuple

from autogqla.spec_resolver import OrderByProperty


class PaginationDetails:

    def __init__(self, before, after, first, last, order_by: Tuple[OrderByProperty]):
        self.before = self._load(before)
        self.after = self._load(after)
        self.first = first
        self.last = last
        self.order_by: Tuple[OrderByProperty] = order_by

    @staticmethod
    def _load(s):
        return tuple(json.loads(base64.b64decode(s.encode()).decode())) if s else None

    @property
    def before_pk(self):
        return self.before[0] if self.before else None

    @property
    def after_pk(self):
        return self.after[0] if self.after else None

    @property
    def before_value(self):
        return self.before[1] if self.before else None

    @property
    def after_value(self):
        return self.after[1] if self.after else None

    def __hash__(self):
        return hash((
            str(self.before),
            str(self.after),
            self.first,
            self.last,
            self.order_by,
        ))

    def __eq__(self, other):
        return type(self) == type(other) and hash(self) == hash(other)
