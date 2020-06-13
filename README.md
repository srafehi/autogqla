# AutoGQLA

Automatically generates a [graphene-python](https://graphene-python.org/) graphql schema from [SQLAlchemy](https://www.sqlalchemy.org/) models.

** **(Experimental/Pre-alpha)** **


## Features

* Automatically creates graphql objects from SQLAlchemy models
* Automatically creates graphql relationships (both simple and [cursor-based](https://relay.dev/graphql/connections.htm)) from SQLAlchemy relationships
* Supports relationship filtering based on the target object attributes and all of its relationships

## Usage

### Setup

Define your SQLAlchemy model:

```python
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship

Base = declarative_base()


class Country(Base):
    __tablename__ = 'country'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)

    states = relationship('State', back_populates='country', uselist=True)


class State(Base):
    __tablename__ = 'state'

    id = Column(Integer, primary_key=True, autoincrement=True)
    country_id = Column(ForeignKey('country.id'))
    name = Column(String, nullable=False)
    population = Column(Integer, nullable=False)

    country: Country = relationship('Country', back_populates='states')
```

Add some dummy data to your model:

```python
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


engine = create_engine('sqlite://')
Base.metadata.create_all(engine)
session_factory = sessionmaker(bind=engine)
session = session_factory()
australia = Country(
    name='Australia',
    states=[
        State(name='New South Wales', population=8_100_000),
        State(name='Victoria', population=6_600_000),
        State(name='Queensland', population=5_100_000),
        State(name='Western Australia', population=2_600_000),
        State(name='South Australia', population=1_750_000),
        State(name='Tasmania', population=550_000),
        State(name='Australian Capital Territory', population=450_000),
        State(name='Northern Territory', population=250_000),
    ],
)
session.add(australia)
session.commit()
session.close()
```

Generate a graphene Schema using your SQLAlchemy models:

```python
import autogqla
import graphene
from autogqla import (
    Schema,
    make_relationship_field,
    make_relationship_resolver,
    make_pagination_field,
    make_pagination_resolver,
)


autogqla.create(base=Base)


class Query(graphene.ObjectType):

    countries = make_relationship_field(model=Country)
    resolve_countries = make_relationship_resolver(model=Country)
    states = make_relationship_field(model=State)
    resolve_states = make_relationship_resolver(model=State)

    paginate_states = make_pagination_field(model=State)
    resolve_paginate_states = make_pagination_resolver(model=State)


schema = Schema(query=Query)
schema.set_session_factory(session_factory=session_factory)
```

### Queries

**Query countries and their states:**

```python
result = schema.execute('''{
  countries {
    name
    states {
      name
    }
  }
}''')
print(result.to_dict())
```
```json
{
  "data": {
    "countries": [
      {
        "name": "Australia",
        "states": [
          {
            "name": "New South Wales"
          },
          {
            "name": "Victoria"
          },
          {
            "name": "Queensland"
          },
          {
            "name": "Western Australia"
          },
          {
            "name": "South Australia"
          },
          {
            "name": "Australian Capital Territory"
          },
          {
            "name": "Northern Territory"
          }
        ]
      }
    ]
  }
}
```

**Query states named Victoria:**

```python
result = schema.execute('''{
  states(where: {name: {eq: "Victoria"}}) {
    name
    country {
      name
    }
  }
}''')
print(result.to_dict())
```
```json
{
  "data": {
    "states": [
      {
        "name": "Victoria",
        "population": 6600000,
        "country": {
          "name": "Australia"
        }
      }
    ]
  }
}
```

**Query states with a population greater than five million:**

```python
result = schema.execute('''{
  countries {
    states: filterStates(where: {population: {ge: 5000000}}) {
      name
      population
    }
  }
}''')
print(result.to_dict())
```
```json
{
  "data": {
    "countries": [
      {
        "states": [
          {
            "name": "New South Wales",
            "population": 8100000
          },
          {
            "name": "Victoria",
            "population": 6600000
          },
          {
            "name": "Queensland",
            "population": 5100000
          }
        ]
      }
    ]
  }
}
```

**Return the first two states with a population greater than 1,000,000:**

```python
result = schema.execute('''{
  paginateStates(first: 2, where: {population: {gt: 1000000}}, orderBy: [POPULATION_ASC]) {
    pageInfo {
      startCursor
      endCursor
      hasNextPage
      hasPreviousPage
    }
    edges {
      cursor
      node {
        name
        population
      }
    }
  }
}''')
print(result.to_dict())
```
```json
{
  "data": {
    "paginateStates": {
      "pageInfo": {
        "startCursor": "WzUsIFsxNzUwMDAwXSwgWyJBU0MiXV0=",
        "endCursor": "WzQsIFsyNjAwMDAwXSwgWyJBU0MiXV0=",
        "hasNextPage": true,
        "hasPreviousPage": false
      },
      "edges": [
        {
          "cursor": "WzUsIFsxNzUwMDAwXSwgWyJBU0MiXV0=",
          "node": {
            "name": "South Australia",
            "population": 1750000
          }
        },
        {
          "cursor": "WzQsIFsyNjAwMDAwXSwgWyJBU0MiXV0=",
          "node": {
            "name": "Western Australia",
            "population": 2600000
          }
        }
      ]
    }
  }
}
```
