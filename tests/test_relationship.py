from graphene import Schema


def test_relationship(schema: Schema):
    result = schema.execute(''' {
        countries {
            name
        }
    }''')
    assert not result.errors
    assert result.data == {
        'countries': [
            {'name': 'Australia'},
            {'name': 'United States'},
        ]
    }


def test_relationship_with_direct_filter_eq(schema: Schema):
    result = schema.execute(''' {
        countries(where: {name: {eq: "Australia"}}) {
            name
        }
    }''')
    assert not result.errors
    assert result.data == {
        'countries': [
            {'name': 'Australia'},
        ]
    }


def test_relationship_with_direct_filter_ne(schema: Schema):
    result = schema.execute(''' {
        countries(where: {name: {ne: "Australia"}}) {
            name
        }
    }''')
    assert not result.errors
    assert result.data == {
        'countries': [
            {'name': 'United States'},
        ]
    }


def test_relationship_with_direct_filter_in(schema: Schema):
    result = schema.execute(''' {
        countries(where: {name: {in: ["Australia", "United States"]}}) {
            name
        }
    }''')
    assert not result.errors
    assert result.data == {
        'countries': [
            {'name': 'Australia'},
            {'name': 'United States'},
        ]
    }


def test_relationship_with_indirect_filter(schema: Schema):
    result = schema.execute(''' {
        countries(where: {states: {name: {eq: "New York"}}}) {
            name
        }
    }''')
    assert not result.errors
    assert result.data == {
        'countries': [
            {'name': 'United States'},
        ]
    }


def test_relationship_child(schema: Schema):
    result = schema.execute(''' {
        countries {
            name
            states {
                internalId
                name
            }
        }
    }''')
    assert not result.errors
    assert result.data == {
        'countries': [
            {
                'name': 'Australia',
                'states': [
                    {'internalId': 1, 'name': 'Victoria'},
                    {'internalId': 2, 'name': 'New South Wales'},
                ]
            },
            {
                'name': 'United States',
                'states': [
                    {'internalId': 3, 'name': 'New York'},
                ]
            },
        ]
    }


def test_relationship_child_with_filter(schema: Schema):
    result = schema.execute(''' {
        countries {
            name
            states: filterStates(where: {name: {ne: "Victoria"}}) {
                internalId
                name
            }
        }
    }''')
    assert not result.errors
    assert result.data == {
        'countries': [
            {
                'name': 'Australia',
                'states': [
                    {'internalId': 2, 'name': 'New South Wales'},
                ]
            },
            {
                'name': 'United States',
                'states': [
                    {'internalId': 3, 'name': 'New York'},
                ]
            },
        ]
    }


def test_relationship_paginate_child_order_by(schema: Schema):
    result = schema.execute(''' {
        countries(where: {name: {eq: "Australia"}}) {
            name
            states: paginateStates(first: 10, orderBy: [NAME_ASC]) {
                edges {
                    node {
                        internalId
                        name
                    }
                }
            }
        }
    }''')
    assert not result.errors
    assert result.data == {
        'countries': [
            {
                'name': 'Australia',
                'states': {
                    'edges': [
                        {
                            'node': {'internalId': 2, 'name': 'New South Wales'}
                        },
                        {
                            'node': {'internalId': 1, 'name': 'Victoria'}
                        },
                    ]
                }
            },
        ]
    }
