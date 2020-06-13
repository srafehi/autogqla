from typing import Union, Optional

import graphene
from sqlalchemy.orm import scoped_session, sessionmaker

from autogqla.base import BaseModel

SessionFactory = Union[scoped_session, sessionmaker]


class Schema(graphene.Schema):

    session_factory: Optional[SessionFactory] = None

    def set_session_factory(self, session_factory: SessionFactory):
        self.session_factory = session_factory

    def execute(self, *args, **kwargs):
        session = self.session_factory() if self.session_factory else None
        if session:
            BaseModel.session_func = lambda: session
        try:
            return super().execute(*args, **kwargs)
        finally:
            if session:
                BaseModel.session_func = None
                if isinstance(self.session_factory, scoped_session):
                    session.remove()
                elif isinstance(self.session_factory, sessionmaker):
                    session.close()
