from threading import local
from typing import Union

import graphene

from .base import create_query_function
from .pagination_connection_field import PaginationConnectionField
from .pagination_details import PaginationDetails
from .pagination_loader import PaginationLoader
from ..base_field import BaseField
from ...spec import RelationshipSpec


class PaginationField(BaseField[RelationshipSpec]):

    _loaders = local()

    def _name(self) -> str:
        return self.spec.name

    def _make_field(self) -> Union[graphene.Field, graphene.List, graphene.NonNull]:
        props = {
            'description': self.spec.column.comment if self.spec.column is not None else None,
            **self.arguments,
            **self.spec.props,
        }
        return PaginationConnectionField(
            self.resolver.collection.for_relationship(self.spec.attribute).connection_type,
            **props,
        )

    def _execute(self, instance, info, first=None, last=None, before=None, after=None, order_by=None, **arguments):
        return self.loader(
            arguments=arguments,
            pagination=PaginationDetails(before, after, first, last, tuple(order_by or ())),
        ).load(instance)

    def loader(self, arguments, pagination) -> PaginationLoader:
        query_func = create_query_function(
            spec=self.spec,
            resolver_collection=self.resolver.collection,
            arguments=arguments,
        )
        return PaginationLoader(
            pagination=pagination,
            model=self.spec.source_model,
            member=self.spec.model_attribute,
            query_func=query_func,
            session_func=self.session_func,
        )
