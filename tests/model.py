from __future__ import annotations

from typing import List

from sqlalchemy import Integer, Column, String, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


class Country(Base):
    __tablename__ = 'country'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)

    states: List[State] = relationship('State', back_populates='country', uselist=True)


class State(Base):
    __tablename__ = 'state'

    id = Column(Integer, primary_key=True, autoincrement=True)
    country_id = Column(Integer, ForeignKey('country.id'))
    name = Column(String(100), nullable=False)

    country: Country = relationship('Country', back_populates='states')
    suburbs: List[Suburb] = relationship('Suburb', back_populates='state', uselist=True)


class Suburb(Base):
    __tablename__ = 'suburb'

    id = Column(Integer, primary_key=True, autoincrement=True)
    state_id = Column(Integer, ForeignKey('state.id'))
    name = Column(String(100), nullable=False)

    state: State = relationship('State', back_populates='suburbs')
    places: List[Place] = relationship('Place', back_populates='suburb', uselist=True)


class Place(Base):
    __tablename__ = 'place'

    id = Column(Integer, primary_key=True, autoincrement=True)
    suburb_id = Column(Integer, ForeignKey('suburb.id'))
    name = Column(String(100), nullable=False)
    address = Column(String(100), nullable=True)

    suburb: Suburb = relationship('Suburb', back_populates='places')


def build_models() -> List[Country]:
    return [
        Country(name='Australia', states=[
            State(name='Victoria', suburbs=[
                Suburb(name='Melbourne', places=[
                    Place(name='Queen Victoria Market', address='Queen St, Melbourne VIC 3000'),
                ])
            ]),
            State(name='New South Wales', suburbs=[
                Suburb(name='Sydney', places=[
                    Place(name='Sydney Opera House', address='Bennelong Point, Sydney NSW 2000'),
                ])
            ])
        ]),
        Country(name='United States', states=[
            State(name='New York', suburbs=[
                Suburb(name='Manhattan', places=[
                    Place(name='Central Park', address='Manhattan, New York City, United States')
                ])
            ])
        ]),
    ]
