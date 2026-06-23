from elasticsearch_dsl import Search, Q


def get_info(collection):
    dims_dict = {}
    s = Search(index="collections", doc_type="doc").query(
        Q("term", collection=collection)
    ).extra(size=1000)
    response = s.execute()

    for hit in response:
        for dim in hit.dimensions:
            name = dim['name']
            value = dim['value']
            if name not in dims_dict:
                dims_dict[name] = []
            if value is not None:
                dims_dict[name].append(value)

    for k in dims_dict:
        dims_dict[k] = list(set(dims_dict[k]))

    return dims_dict


def get_series(collection_id, concept_id, dimensiones, valores, mode):
    queries = [Q("term", collection=collection_id)]

    if concept_id:
        queries.append(Q("term", concept=concept_id))

    for dim, val in zip(dimensiones, valores):
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

    s = Search(index="collections", doc_type="doc").query(Q("bool", must=queries))
    response = s.execute()
    return [hit.id for hit in response]