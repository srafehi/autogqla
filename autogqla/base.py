from __future__ import annotations

from typing import Dict, Type

import graphene
from sqlalchemy.ext.declarative import DeclarativeMeta

from . import fields
from .spec import ModelSpec
from .spec_resolver import ModelSpecResolver, ResolverCollection


class BaseModel(graphene.ObjectType):
    __spec__: ModelSpec
    _models: Dict[str, Type[BaseModel]] = {}
    session_func = None
    resolver_collection: ResolverCollection = ResolverCollection()

    def __init_subclass__(cls, **kwargs):
        model = cls.__spec__.model
        cls._models[model.__name__] = cls
        cls.resolver_collection.add(
            ModelSpecResolver(
                model_spec=cls.__spec__,
                node=cls,
                collection=cls.resolver_collection,
            )
        )
        for field in cls.__create_simple_fields():
            cls.__apply(field=field)

    @classmethod
    def create_all(cls):
        for graphql_object in cls._models.values():
            cls.resolver_collection.for_model(graphql_object.__spec__.model).resolve_attributes()

        for graphql_object in cls._models.values():
            cls.resolver_collection.for_model(graphql_object.__spec__.model).resolve_types()

        for graphql_object in cls._models.values():
            graphql_object.create()

    @classmethod
    def _get_session(cls):
        return cls.session_func()

    @classmethod
    def create(cls):
        for field in cls.__create_simple_fields():
            cls.__apply(field=field)
        for prefix, field in cls.__create_relationship_fields():
            cls.__apply(field=field, prefix=prefix)
        super().__init_subclass__()

    @classmethod
    def __create_simple_fields(cls):
        model = cls.__spec__.model
        resolver = cls.resolver_collection.for_model(model)
        for field_spec in resolver.field_specs_dict.values():
            if field_spec.is_primary_key():
                yield fields.IdentifierField(cls._get_session, resolver=resolver, spec=field_spec)
            yield fields.SimpleField(cls._get_session, resolver=resolver, spec=field_spec)

    @classmethod
    def __create_relationship_fields(cls):
        model = cls.__spec__.model
        resolver = cls.resolver_collection.for_model(model)
        for relationship_spec in resolver.relationship_specs_dict.values():
            if not relationship_spec.attribute.uselist and len(relationship_spec.attribute.local_columns) == 1:
                required = not list(relationship_spec.attribute.local_columns)[0].nullable
            else:
                required = False
            yield '', fields.RelationshipField(cls._get_session, resolver=resolver, spec=relationship_spec, arguments={
                'required': required,
            })
            if relationship_spec.attribute.uselist:
                where = cls.resolver_collection.for_relationship(relationship_spec.attribute).lazy_where_input_type()
                assert where, (relationship_spec, relationship_spec.attribute)
                if resolver.model_spec.relationships.filterable.should_include(relationship_spec.name):
                    yield 'filter_', fields.RelationshipField(cls._get_session, resolver=resolver, spec=relationship_spec, arguments={
                        'where': graphene.Argument(where),
                    })
                if resolver.model_spec.relationships.paginated.should_include(relationship_spec.name):
                    target_resolver = cls.resolver_collection.for_relationship(relationship_spec.attribute)
                    yield 'paginate_', fields.PaginationField(cls._get_session, resolver=resolver, spec=relationship_spec, arguments={
                        'where': graphene.Argument(where),
                        'order_by': graphene.Argument(graphene.List(target_resolver.order_by_enum)),
                    })

    @classmethod
    def __apply(cls, field, prefix=''):
        setattr(cls, f'{prefix}{field.name}', field.field)
        setattr(cls, f'resolve_{prefix}{field.name}', field.__call__)

    @classmethod
    def load_base(cls, base: DeclarativeMeta):
        for base_class in base._decl_class_registry.values():
            if isinstance(base_class, type) and issubclass(base_class, base):
                class_name = base_class.__name__
                if class_name not in cls.resolver_collection.resolvers:
                    type(class_name, (cls,), {'__spec__': ModelSpec(model=base_class)})

        cls.create_all()


def create(base: DeclarativeMeta):
    BaseModel.load_base(base=base)
