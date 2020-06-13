import json
from threading import local
from typing import Union

import graphene

from .base import create_query_function
from .relationship_loader import RelationshipLoader
from ..base_field import BaseField
from ...spec import RelationshipSpec


class RelationshipField(BaseField[RelationshipSpec]):

    _loaders = local()

    def _name(self) -> str:
        return self.spec.name

    def _make_field(self) -> Union[graphene.Field, graphene.List, graphene.NonNull]:
        props = {
            'description': self.spec.column.comment if self.spec.column is not None else None,
            **self.arguments,
            **self.spec.props,
        }
        target_node = self.resolver.collection.for_relationship(self.spec.attribute).node
        if self.spec.attribute.uselist:
            list_field = graphene.List(graphene.NonNull(target_node))
            props = {k: v for k, v in props.items() if v is not None}
            return graphene.Field(graphene.NonNull(list_field), **props)
        else:
            return graphene.Field(target_node, **props)

    def _execute(self, instance, info, **arguments):
        return self.loader(arguments).load(instance)

    def loader(self, arguments) -> RelationshipLoader:
        if not hasattr(self._loaders, 'loaders'):
            self._loaders.loaders = {}

        key = self.spec.source_model_name, self.name, json.dumps(arguments, default=str)
        if key not in self._loaders.loaders:
            query_func = create_query_function(
                spec=self.spec,
                resolver_collection=self.resolver.collection,
                arguments=arguments,
            )
            self._loaders.loaders[key] = RelationshipLoader(
                self.spec.source_model,
                self.spec.model_attribute,
                query_func=query_func,
                session_func=self.session_func,
            )
        return self._loaders.loaders[key]
