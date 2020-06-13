import graphene

from autogqla.base import BaseModel
from autogqla.fields.connections.base import apply_query_condition
from autogqla.fields.connections.pagination_connection_field import PaginationConnectionField
from autogqla.fields.connections.pagination_details import PaginationDetails
from autogqla.fields.connections.pagination_helpers import paginate


def make_pagination_field(model):
    resolver = BaseModel.resolver_collection.for_model(model)
    return PaginationConnectionField(
        resolver.connection_type,
        where=graphene.Argument(resolver.where_input_type),
        order_by=graphene.Argument(graphene.List(resolver.order_by_enum)),
    )


def make_pagination_resolver(model):
    def execute(_, _info, first=None, last=None, before=None, after=None, order_by=None, **arguments):
        pagination = PaginationDetails(before, after, first, last, tuple(order_by or ()))
        session = BaseModel.session_func()
        resolver = BaseModel.resolver_collection.for_model(model)
        query = session.query(model)

        query = apply_query_condition(query=query, resolver=resolver, arguments=arguments)
        return paginate(model, query, pagination)

    return execute


def make_relationship_field(model):
    resolver = BaseModel.resolver_collection.for_model(model)
    return graphene.List(
        graphene.NonNull(resolver.node),
        required=True,
        where=graphene.Argument(resolver.where_input_type),
    )


def make_relationship_resolver(model):
    def execute(_, _info, **arguments):
        session = BaseModel.session_func()
        resolver = BaseModel.resolver_collection.for_model(model)
        query = session.query(model)

        query = apply_query_condition(query=query, resolver=resolver, arguments=arguments)
        return query.all()

    return execute
