from __future__ import annotations
import enum
from dataclasses import dataclass, field
from typing import Dict, Tuple, Any

import graphene
import sqlalchemy
from sqlalchemy import inspect
from sqlalchemy.orm import Mapper, ColumnProperty, RelationshipProperty

from . import condition_constructor
from .spec import ModelSpec, FieldSpec, RelationshipSpec


@dataclass(frozen=True, order=True)
class OrderByProperty:
    key: str
    direction: str
    model: Any
    joins: Tuple = field(default_factory=tuple)


class ResolverCollection:

    def __init__(self):
        self.resolvers: Dict[str, ModelSpecResolver] = {}

    def add(self, resolver: ModelSpecResolver):
        self.resolvers[resolver.sqla_model.__name__] = resolver

    def for_relationship(self, relationship: RelationshipProperty) -> ModelSpecResolver:
        return self.for_model(relationship.mapper.entity)

    def for_model(self, model) -> ModelSpecResolver:
        return self.resolvers[model.__name__]

    def has_spec_for_model(self, model) -> bool:
        try:
            return bool(self.for_model(model))
        except KeyError:
            return False

    def has_spec_for_relationship(self, relationship: RelationshipProperty) -> bool:
        try:
            return bool(self.for_relationship(relationship))
        except KeyError:
            return False


class ModelSpecResolver:

    FIELD_MAPPING = {
        sqlalchemy.String: graphene.String,
        sqlalchemy.Integer: graphene.Int,
        sqlalchemy.Float: graphene.Float,
        sqlalchemy.DateTime: graphene.DateTime,
        sqlalchemy.Date: graphene.Date,
        sqlalchemy.Boolean: graphene.Boolean,
        sqlalchemy.JSON: graphene.JSONString,
        sqlalchemy.Binary: graphene.String,
        sqlalchemy.Enum: graphene.String,
        sqlalchemy.Text: graphene.String,
    }

    def __init__(self, model_spec, node, collection: ResolverCollection):
        self.node = node
        self.model_spec: ModelSpec = model_spec
        self.model_spec.name = self.model_spec.name or self.node.__name__
        self._resolved_attributes = False
        self._resolved_types = False
        self.field_specs_dict: Dict[str, FieldSpec] = {}
        self.relationship_specs_dict: Dict[str, RelationshipSpec] = {}
        self.where_input_type = None
        self.order_by_enum = None
        self.connection_type = None
        self.collection: ResolverCollection = collection

    @property
    def sqla_model(self):
        return self.model_spec.model

    @property
    def model_mapper(self) -> Mapper:
        return inspect(self.sqla_model).mapper

    def make_fields(self):
        return [
            field.field_type(**{
                'description': field.column.comment,
                'required': not field.column.nullable,
                **field.props
            })
            for field in self.field_specs_dict.values()
        ]

    def _build_fields(self):
        column: ColumnProperty
        for column in self.model_mapper.column_attrs:
            name = column.key
            is_pk = column.columns[0].primary_key
            if not is_pk and not self.model_spec.fields.should_include(name):
                continue

            spec = self.model_spec.fields.specs.get(name) or FieldSpec()
            spec.attribute = column
            if is_pk:
                spec.name = 'internal_id'
            elif not spec.name:
                spec.name = name

            if not spec.field_type:
                sqla_type = type(column.columns[0].type)
                spec.field_type = self.FIELD_MAPPING[sqla_type]

            self.field_specs_dict[spec.name] = spec

    def _build_relationships(self):
        relationship: RelationshipProperty
        for relationship in self.model_mapper.relationships.values():
            relationship_name = relationship.key
            if not self.model_spec.relationships.should_include(relationship_name):
                continue

            if not self.collection.has_spec_for_relationship(relationship):
                continue

            relationship_spec = self.model_spec.relationships.specs.get(relationship_name) or RelationshipSpec()
            relationship_spec.attribute = relationship
            if not relationship_spec.name:
                relationship_spec.name = relationship_name

            self.relationship_specs_dict[relationship_spec.name] = relationship_spec

    def lazy_where_input_type(self):
        return lambda: self.where_input_type

    def _build_where_input_type(self):
        if self.where_input_type:
            return

        name = self._make_name('WhereFilter')

        attributes = {
            'and_': graphene.List(lambda: self.where_input_type, name='and'),
            'or_': graphene.List(lambda: self.where_input_type, name='or'),
            'id': condition_constructor.StringFilter(),
        }

        for relationship in self.relationship_specs_dict.values():
            if self.model_spec.relationships.where.should_include(relationship.name):
                if not self.collection.has_spec_for_relationship(relationship.attribute):
                    continue
                relationship_model_spec = self.collection.for_relationship(relationship.attribute)
                attributes[relationship.name] = graphene.Field(relationship_model_spec.lazy_where_input_type())

        for field in self.field_specs_dict.values():
            if self.model_spec.fields.where.should_include(field.name):
                attributes[field.name] = graphene.Field(condition_constructor.FILTER_MAPPING[field.field_type])

        self.where_input_type = type(name, (graphene.InputObjectType,), attributes)

    def _build_order_by_enum(self):
        if self.order_by_enum:
            return
        enum_items = {}
        for field_spec in self.field_specs_dict.values():
            if self.model_spec.fields.order_by.should_include(field_spec.name):
                enum_items[f'{field_spec.name.upper()}_ASC'] = OrderByProperty(
                    key=field_spec.attribute.key,
                    direction='ASC',
                    model=self.sqla_model,
                )
                enum_items[f'{field_spec.name.upper()}_DESC'] = OrderByProperty(
                    key=field_spec.attribute.key,
                    direction='DESC',
                    model=self.sqla_model,
                )

        for relationship in self.relationship_specs_dict.values():
            resolver = self.collection.for_relationship(relationship.attribute)
            for field_spec in resolver.field_specs_dict.values():
                if resolver.model_spec.fields.order_by.should_include(field_spec.name):
                    enum_items[f'{relationship.name.upper()}__{field_spec.name.upper()}_ASC'] = OrderByProperty(
                        key=field_spec.attribute.key,
                        direction='ASC',
                        model=resolver.sqla_model,
                        joins=(relationship.attribute,),
                    )
                    enum_items[f'{relationship.name.upper()}__{field_spec.name.upper()}_DESC'] = OrderByProperty(
                        key=field_spec.attribute.key,
                        direction='DESC',
                        model=resolver.sqla_model,
                        joins=(relationship.attribute,),
                    )

        self.order_by_enum = graphene.Enum.from_enum(
            enum.Enum(self._make_name('OrderEnum'), enum_items)
        )

    def _build_connection_type(self):
        if self.connection_type:
            return

        class Meta:
            node = graphene.NonNull(self.node)

        cls = type(
            self._make_name('Connection'),
            (graphene.relay.Connection,),
            {'Meta': Meta}
        )

        self.connection_type = graphene.NonNull(cls)

    def resolve_attributes(self):
        if not self._resolved_attributes:
            self._build_fields()
            self._build_relationships()
        self._resolved_attributes = True

    def resolve_types(self):
        if not self._resolved_types:
            self._build_where_input_type()
            self._build_order_by_enum()
            self._build_connection_type()
        self._resolved_types = True

    def _make_name(self, suffix):
        return f'{self.model_spec.name}{suffix}'
