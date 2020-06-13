import graphene

import autogqla
from tests.model import Country


class Query(graphene.ObjectType):
    countries = autogqla.objects.helpers.make_relationship_field(Country)
    resolve_countries = autogqla.objects.helpers.make_relationship_resolver(Country)

    paginate_countries = autogqla.objects.helpers.make_pagination_field(Country)
    resolve_paginate_countries = autogqla.objects.helpers.make_pagination_resolver(Country)
