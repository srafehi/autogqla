import graphene

import autogqla
from tests.model import Country, State


class Query(graphene.ObjectType):
    countries = autogqla.objects.helpers.make_relationship_field(Country)
    resolve_countries = autogqla.objects.helpers.make_relationship_resolver(Country)

    paginate_countries = autogqla.objects.helpers.make_pagination_field(Country)
    resolve_paginate_countries = autogqla.objects.helpers.make_pagination_resolver(Country)

    states = autogqla.objects.helpers.make_relationship_field(State)
    resolve_states = autogqla.objects.helpers.make_relationship_resolver(State)

    paginate_states = autogqla.objects.helpers.make_pagination_field(State)
    resolve_paginate_states = autogqla.objects.helpers.make_pagination_resolver(State)
