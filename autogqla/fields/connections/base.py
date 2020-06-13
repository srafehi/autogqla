from functools import partial

from autogqla.condition_constructor import construct_condition
from autogqla.spec import RelationshipSpec
from autogqla.spec_resolver import ResolverCollection, ModelSpecResolver


def unique_join(query, join_attr):
    join_model = join_attr.mapper.entity
    if join_model in (d['entity'] for d in query.column_descriptions):
        return query
    if join_model in (c.entity for c in getattr(query, '_join_entities')):
        return query
    return query.join(getattr(join_attr.parent.entity, join_attr.key))


def apply_query_condition(query, resolver: ModelSpecResolver, arguments: dict):
    where = arguments.get('where')
    joins, where_filter = construct_condition(resolver, where)
    if where_filter is not None:
        for join_attr in joins:
            query = unique_join(query, join_attr)
    return query.filter(where_filter) if where_filter is not None else query


def create_query_function(spec: RelationshipSpec, arguments: dict, resolver_collection: ResolverCollection):
    node = resolver_collection.for_relationship(spec.attribute).node
    query_func = getattr(node, f'query_{spec.name}', apply_query_condition)
    resolver = resolver_collection.for_model(spec.target_model)
    query_func = partial(query_func, resolver=resolver, arguments=arguments)
    return query_func
