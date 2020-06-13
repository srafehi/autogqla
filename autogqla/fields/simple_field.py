import graphene

from . import BaseField
from autogqla.spec import FieldSpec


class SimpleField(BaseField[FieldSpec]):

    def _name(self) -> str:
        return self.spec.name

    def _make_field(self) -> graphene.Scalar:
        props = {
            'description': self.spec.column.comment,
            'required': not self.spec.column.nullable,
            **self.spec.props
        }
        return self.spec.field_type(**props)

    def _execute(self, instance, info, **arguments):
        return getattr(instance, self.spec.key)
