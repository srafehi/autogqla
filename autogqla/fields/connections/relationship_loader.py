from promise import Promise

from autogqla.fields.connections.base_loader import ConnectionLoader


class RelationshipLoader(ConnectionLoader):

    def batch_load_fn(self, models):
        return Promise.resolve(
            self._group_results(
                models,
                self._make_query(models).all(),
                return_child=True,
            )
        )