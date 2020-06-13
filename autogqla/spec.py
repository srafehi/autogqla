from __future__ import annotations

from typing import Dict, Optional, List, TypeVar, Generic, Union

from sqlalchemy import Column
from sqlalchemy.orm import RelationshipProperty, ColumnProperty

T = TypeVar('T')


def _validate_include_exclude(instance, include, exclude):
    if include and exclude:
        raise Exception(f' cannot provide both include and exclude to {type(instance)}')


class ModelSpec:

    def __init__(
            self,
            model,
            name: str = None,
            fields: FieldsSpec = None,
            relationships: RelationshipsSpec = None,
    ):
        self.name = name
        self.model = model
        self.fields: FieldsSpec = fields or FieldsSpec()
        self.relationships: RelationshipsSpec = relationships or RelationshipsSpec()

    @property
    def model_name(self):
        return self.model.__name__


class AttributeSpec(Generic[T]):

    def __init__(
            self,
            name: Optional[str] = None,
            props: Dict = None,
            attribute: Optional[T] = None,
    ):
        self.name = name
        self.props = props or {}
        self.attribute: Optional[T] = attribute

    @property
    def key(self) -> str:
        return self.attribute.key

    @property
    def model_attribute(self):
        return getattr(self.attribute.parent.entity, self.attribute.key)

    @property
    def source_model(self):
        return self.attribute.parent.entity

    @property
    def source_model_name(self):
        return self.source_model.__name__


class FieldSpec(AttributeSpec[ColumnProperty]):

    def __init__(
            self,
            field_type: Optional = None,
            *args,
            **kwargs,
    ):
        super().__init__(*args, **kwargs)
        self.field_type = field_type

    def is_primary_key(self):
        return self.column.primary_key

    @property
    def column(self) -> Column:
        return self.attribute.columns[0]


class RelationshipSpec(AttributeSpec[RelationshipProperty]):

    @property
    def column(self) -> Optional[Column]:
        if len(self.attribute.local_columns) == 1:
            return list(self.attribute.local_columns)[0]

    @property
    def target_model(self):
        return self.attribute.mapper.entity


class AttributeCollectionSpec(Generic[T]):

    def __init__(
            self,
            include: Optional[List[str]] = None,
            exclude: Optional[List[str]] = None,
            specs: Optional[Dict[str, Union[T, dict]]] = None,
            where: Optional[Union[WhereSpec, List[str]]] = None,
    ):
        _validate_include_exclude(self, include, exclude)
        GenericClass = self.__orig_bases__[0].__args__[0]

        self.include: List[str] = include or []
        self.exclude: List[str] = exclude or []
        self.specs: Dict[str, T] = {
            key: value if isinstance(value, GenericClass) else GenericClass(props=value or {})
            for key, value in (specs or {}).items()
        }
        self.where: WhereSpec = WhereSpec.create(where)

    def should_include(self, name) -> bool:
        if self.include:
            return bool(name in self.include)
        else:
            return bool(name not in self.exclude)

    def props_for_name(self, name) -> Dict:
        return self.specs[name].props if name in self.specs else {}


class FieldsSpec(AttributeCollectionSpec[FieldSpec]):

    def __init__(
            self,
            order_by: Optional[Union[OrderBySpec, List[str]]] = None,
            *args,
            **kwargs
    ):
        super().__init__(*args, **kwargs)
        self.order_by: OrderBySpec = OrderBySpec.create(order_by)


class RelationshipsSpec(AttributeCollectionSpec[RelationshipSpec]):

    def __init__(
            self,
            basic: Optional[Union[BasicSpec, List[str]]] = None,
            filterable: Optional[Union[OrderBySpec, List[str]]] = None,
            paginated: Optional[Union[PaginatedSpec, List[str]]] = None,
            *args,
            **kwargs
    ):
        super().__init__(*args, **kwargs)
        self.basic: BasicSpec = BasicSpec.create(basic)
        self.filterable: FilterableSpec = FilterableSpec.create(filterable)
        self.paginated: PaginatedSpec = PaginatedSpec.create(paginated)


class IncludeExclude:

    def __init__(
            self,
            include: List[str] = None,
            exclude: List[str] = None,
    ):
        _validate_include_exclude(self, include, exclude)
        self.include = include or []
        self.exclude = exclude or []

    def should_include(self, name) -> bool:
        if self.include:
            return bool(name in self.include)
        else:
            return bool(name not in self.exclude)

    @classmethod
    def create(cls, spec):
        return spec if isinstance(spec, cls) else cls(include=spec or [])


class OrderBySpec(IncludeExclude):
    pass


class WhereSpec(IncludeExclude):
    pass


class FilterableSpec(IncludeExclude):
    pass


class BasicSpec(IncludeExclude):
    pass


class PaginatedSpec(IncludeExclude):
    pass
