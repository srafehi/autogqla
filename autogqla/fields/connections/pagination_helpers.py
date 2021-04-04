from sqlalchemy.orm import Query

from autogqla.fields.connections.base import unique_join
from autogqla.fields.connections.pagination_details import PaginationDetails
from autogqla.spec_resolver import OrderByProperty


def order_clause(attribute, direction, reverse):
    if reverse:
        direction = 'ASC' if direction == 'DESC' else 'DESC'

    return attribute.asc().nullsfirst() if direction == 'ASC' else attribute.desc().nullslast()


def pagination_condition(cursor_props, reverse):
    [[order_by_prop, value], *remaining] = cursor_props
    name, direction, model = order_by_prop.key, order_by_prop.direction, order_by_prop.model
    attribute = getattr(model, name)

    if reverse:
        direction = 'ASC' if direction == 'DESC' else 'DESC'

    if value is None:
        if direction == 'ASC':
            exp_cur_nxt = attribute.is_(None) | attribute.isnot(None)
            exp_nxt = attribute.isnot(None)
        else:
            exp_cur_nxt = attribute.is_(None)
            exp_nxt = attribute.is_(None) & attribute.isnot(None)
    else:
        if direction == 'ASC':
            exp_cur_nxt = attribute >= value
            exp_nxt = attribute > value
        else:
            exp_cur_nxt = (attribute <= value) | attribute.is_(None)
            exp_nxt = (attribute < value) | attribute.is_(None)

    if remaining:
        return exp_cur_nxt & (exp_nxt | pagination_condition(remaining, reverse))
    else:
        return exp_nxt


def paginate(model, query: Query, pagination: PaginationDetails):

    if pagination.first is not None:
        reverse = False
    elif pagination.last is not None:
        reverse = True
    else:
        raise Exception('first or last not specified')

    order_by_joins = []
    order_by_statements = []
    order_by_columns = []
    for order_by_prop in pagination.order_by:
        attribute = getattr(order_by_prop.model, order_by_prop.key)
        order_by_statements.append(order_clause(attribute, order_by_prop.direction, reverse))
        order_by_joins.extend(order_by_prop.joins)
        order_by_columns.append(attribute)
    order_by_statements.append(order_clause(model.id, 'ASC', reverse))

    for join in order_by_joins:
        query = unique_join(query, join)

    for column in order_by_columns:
        query = query.add_columns(column.label(f'_O_{abs(id(column.class_.__name__))}_{abs(id(column.key))}'))
    query = query.add_columns(model.id.label('id'))

    if not reverse and pagination.after:
        order_columns = list(zip(pagination.order_by, pagination.after_value))
        order_columns.append((OrderByProperty('id', 'ASC', model), pagination.after_pk))
        query = query.filter(pagination_condition(order_columns, reverse))
    if reverse and pagination.before:
        order_columns = list(zip(pagination.order_by, pagination.before_value))
        order_columns.append((OrderByProperty('id', 'ASC', model), pagination.before_pk))
        query = query.filter(pagination_condition(order_columns, reverse))

    limit_amount = (pagination.last if reverse else pagination.first) or 10
    query = query.order_by(*order_by_statements).limit(limit_amount + 1)

    return query.all()
