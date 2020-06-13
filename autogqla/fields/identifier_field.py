import graphene
from graphql_relay import to_global_id

from autogqla.fields import BaseField
from autogqla.spec import FieldSpec


class IdentifierField(BaseField[FieldSpec]):

    def _name(self) -> str:
        return 'id'

    def _make_field(self) -> graphene.Scalar:
        return graphene.ID()

    def _execute(self, instance, info, **arguments):
        value = getattr(instance, self.spec.key)
        return to_global_id(self.resolver.model_spec.name, str(value))
