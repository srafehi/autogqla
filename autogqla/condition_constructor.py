from __future__ import annotations
import base64
import operator
from functools import reduce

import graphene

from . import spec_resolver


class StringFilter(graphene.InputObjectType):
    eq = graphene.String()
    ne = graphene.String()
    starts_with = graphene.String()
    ends_with = graphene.String()
    contains = graphene.String()
    like = graphene.String()
    in_ = graphene.List(graphene.String, name="in")
    not_in = graphene.List(graphene.String)
    is_null = graphene.Boolean()


class BooleanFilter(graphene.InputObjectType):
    eq = graphene.Boolean()
    ne = graphene.Boolean()
    is_null = graphene.Boolean()


class IntFilter(graphene.InputObjectType):
    eq = graphene.Int()
    ne = graphene.Int()
    gt = graphene.Int()
    ge = graphene.Int()
    lt = graphene.Int()
    le = graphene.Int()
    in_ = graphene.List(graphene.Int, name="in")
    not_in = graphene.List(graphene.String)
    is_null = graphene.Boolean()


class FloatFilter(graphene.InputObjectType):
    eq = graphene.Float()
    ne = graphene.Float()
    gt = graphene.Float()
    ge = graphene.Float()
    lt = graphene.Float()
    le = graphene.Float()
    in_ = graphene.List(graphene.Float, name="in")
    not_in = graphene.List(graphene.String)
    is_null = graphene.Boolean()


class DateTimeFilter(graphene.InputObjectType):
    eq = graphene.DateTime()
    ne = graphene.DateTime()
    gt = graphene.DateTime()
    ge = graphene.DateTime()
    lt = graphene.DateTime()
    le = graphene.DateTime()
    is_null = graphene.Boolean()


class DateFilter(graphene.InputObjectType):
    eq = graphene.Date()
    ne = graphene.Date()
    gt = graphene.Date()
    ge = graphene.Date()
    lt = graphene.Date()
    le = graphene.Date()
    is_null = graphene.Boolean()


FILTER_MAPPING = {
    graphene.String: StringFilter,
    graphene.Float: FloatFilter,
    graphene.Int: IntFilter,
    graphene.Boolean: BooleanFilter,
    graphene.DateTime: DateTimeFilter,
    graphene.Date: DateFilter,
}

OP_CODE_MAPPING = {
    'eq': operator.eq,
    'ne': operator.ne,
    'gt': operator.gt,
    'ge': operator.ge,
    'lt': operator.lt,
    'le': operator.le,
    'in_': lambda a, b: a.in_(b),
    'not_in': lambda a, b: ~a.in_(b),
    'is_null': lambda a, b: a.is_(None) if b else a.isnot(None),
    'starts_with': lambda a, b: a.like(f'{b}%'),
    'ends_with': lambda a, b: a.like(f'%{b}'),
    'contains': lambda a, b: a.like(f'%{b}%'),
    'like': lambda a, b: a.like(b),
}


def apply_operand_to_conditions(resolver: 'spec_resolver.ModelSpecResolver', operand, conditions_dict: dict):
    joins = []
    expressions = []
    for item in conditions_dict:
        item_joins, item_expressions = construct_condition(resolver, item)
        joins.extend(item_joins)
        if item_expressions is not None:
            expressions.append(item_expressions)
    return joins, reduce(operand, expressions)


def construct_condition(resolver: 'spec_resolver.ModelSpecResolver', filter_dict: dict):
    filter_dict = dict(filter_dict or {})
    joins = []
    expressions = []

    for operand, conditions_key in ((operator.or_, 'or_'), (operator.and_, 'and_')):
        conditions_dict = filter_dict.pop(conditions_key, None)
        if conditions_dict:
            operand_joins, operand_expression = apply_operand_to_conditions(
                resolver,
                operand,
                conditions_dict,
            )
            joins.extend(operand_joins)
            expressions.append(operand_expression)

    for attribute_name, condition in filter_dict.items():
        if attribute_name in resolver.relationship_specs_dict:
            relationship_spec = resolver.relationship_specs_dict[attribute_name]
            condition_joins, condition_expression = construct_condition(
                resolver.collection.for_model(relationship_spec.target_model),
                condition,
            )
            joins.append(relationship_spec.model_attribute)
            joins.extend(condition_joins)
            expressions.append(condition_expression)

        elif attribute_name in resolver.field_specs_dict:
            field_spec = resolver.field_specs_dict[attribute_name]
            for op_code, value in condition.items():
                if field_spec.name == 'id':
                    _, value = base64.b64decode(value).decode().split(':', 1)
                expressions.append(OP_CODE_MAPPING[op_code](field_spec.model_attribute, value))

    merged_expressions = (reduce(operator.and_, expressions) if expressions else None)
    return joins, merged_expressions
