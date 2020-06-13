import pytest
from graphene import Schema
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from autogqla import create, Schema
from tests.model import Base, build_models


@pytest.fixture(scope='session', autouse=True)
def session_maker():
    engine = create_engine('sqlite://')
    Base.metadata.create_all(engine)
    yield sessionmaker(bind=engine)


@pytest.fixture(scope='session', autouse=True)
def init(session_maker):
    create(Base)
    session = session_maker()
    session.add_all(build_models())
    session.commit()
    session.close()


@pytest.fixture(autouse=True)
def schema(session_maker):
    from tests.query import Query

    schema = Schema(query=Query)
    schema.set_session_factory(session_factory=session_maker)
    return schema
