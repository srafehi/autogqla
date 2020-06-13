from collections import defaultdict

from promise.dataloader import DataLoader
from sqlalchemy import orm
from sqlalchemy.orm import Query, Load


class ConnectionLoader(DataLoader):

    def __init__(self, model, member, query_func, session_func, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.model = model
        self.member = member
        self.query_func = query_func
        self.session = session_func()

    @property
    def target_model(self):
        return self.member.prop.mapper.entity

    def _make_query(self, models) -> Query:
        ids = {model.id for model in models}
        id_filter = self.model.id.in_(ids)

        query = self.session.query(self.target_model, self.model).join(self.member).filter(id_filter).options(
            Load(self.model).load_only('id'),
            orm.contains_eager(self.member),
        )
        return self.query_func(query)

    def _group_results(self, models, results, return_child=True):
        mapping = defaultdict(list)
        for result in results:
            child, parent = result[:2]
            mapping[parent.id].append(child if return_child else result)

        results = []
        for model in models:
            children = mapping[model.id]
            if not self.member.prop.uselist:
                children = children[0] if children else None
            results.append(children)

        return results
