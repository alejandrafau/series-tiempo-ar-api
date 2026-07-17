from elasticsearch_dsl import Search, Q


def get_details(ids):
    s = Search(index="collections", doc_type="doc").query(
        Q("terms", id=ids)
    ).extra(size=len(ids))
    response = s.execute()
    return [
        {
            'id': hit.id,
            'collection': hit.collection,
            'concept': hit.concept,
            'dimensions': [{'name': d.name, 'value': d.value} for d in hit.dimensions],
        }
        for hit in response
    ]


DEFAULT_SIZE = 100


def get_series(collection_id, concept_id, filtros, mode):
    queries = []

    if collection_id:
        queries.append(Q("term", collection=collection_id))

    if concept_id:
        queries.append(Q("term", concept=concept_id))

    for dim, val in filtros.items():
        if isinstance(val, list):
            nested_q = Q("bool", must=[
                Q("term", dimensions__name=dim),
                Q("terms", dimensions__value=val),
            ])
        else:
            nested_q = Q("bool", must=[
                Q("term", dimensions__name=dim),
                Q("term", dimensions__value=val),
            ])
        queries.append(Q("nested", path="dimensions", query=nested_q))

    s = Search(index="collections", doc_type="doc")
    if queries:
        s = s.query(Q("bool", must=queries))
    s = s.extra(size=DEFAULT_SIZE)
    response = s.execute()
    return [
        {
            'id': hit.id,
            'collection': hit.collection,
            'concept': hit.concept,
            'dimensions': [{'name': d.name, 'value': d.value} for d in hit.dimensions],
        }
        for hit in response
    ]