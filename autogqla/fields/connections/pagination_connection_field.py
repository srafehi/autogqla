import base64
import json

import graphene


class PaginationConnectionField(graphene.relay.ConnectionField):

    @classmethod
    def resolve_connection(cls, connection_type, args, resolved):
        edge_type = connection_type.Edge
        page_info_type = graphene.PageInfo
        attr_order_by = args.get('order_by') or ()

        if args.get('first'):
            reverse = False
        elif args.get('last'):
            reverse = True
        else:
            raise Exception('pagination query requires at least "first" or "last" arguments to be provided.')

        limit_amount = int(args.get('first') or args.get('last'))
        has_next = False
        has_prev = False
        if len(resolved) > limit_amount:
            resolved = resolved[:limit_amount]
            if reverse:
                has_prev = True
            else:
                has_next = True

        if reverse:
            resolved = list(reversed(resolved))

        edges = [
            edge_type(
                node=node[0],
                cursor=base64.b64encode(json.dumps([
                    node[0].id,
                    [getattr(node, f'_O_{abs(id(prop.model.__name__))}_{abs(id(prop.key))}') for prop in attr_order_by],
                    [prop.direction for prop in attr_order_by],
                ], default=str).encode()).decode(),
            )
            for i, node in enumerate(resolved)
        ]

        first_edge_cursor = edges[0].cursor if edges else None
        last_edge_cursor = edges[-1].cursor if edges else None

        return connection_type(
            edges=edges,
            page_info=page_info_type(
                start_cursor=first_edge_cursor,
                end_cursor=last_edge_cursor,
                has_next_page=has_next,
                has_previous_page=has_prev,
            )
        )
