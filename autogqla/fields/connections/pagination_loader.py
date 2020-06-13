from promise import Promise

from autogqla.fields.connections.base_loader import ConnectionLoader
from autogqla.fields.connections.pagination_details import PaginationDetails
from autogqla.fields.connections.pagination_helpers import paginate


class PaginationLoader(ConnectionLoader):

    def __init__(self, pagination: PaginationDetails, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.pagination = pagination

    def batch_load_fn(self, models):
        query = self._make_query(models=models)
        results = paginate(self.target_model, query, self.pagination)
        return Promise.resolve(
            self._group_results(models, results, return_child=False)
        )

