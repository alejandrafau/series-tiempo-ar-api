from elasticsearch_dsl import Search,Q
from elasticsearch_dsl.connections import connections
from elasticsearch_dsl import Index
from elasticsearch import Elasticsearch


def get_info(collection):
    tuplas_disponibles = []
    atributos_dict = {}

    q1 = Q("term", collection=collection)
    s = Search(index="collections", doc_type="doc").query(Q("bool", must=q1)).extra(size=1000)
    response = s.execute()

    for hit in response:
        for element in hit.atributos:
            variable = element['variable']
            valor = element['valor']
            if variable not in atributos_dict:
                atributos_dict[variable] = []
            atributos_dict[variable].append(valor)

    for k in atributos_dict:
        atributos_dict[k] = list(set(atributos_dict[k]))

    return atributos_dict



def get_series(collection,variables,valores,modo):
    busquedas = []
    try:
      tuplas_a_buscar = list(zip(variables,valores))
      q1 = Q("term", collection = collection)
      busquedas.append(q1)
      for element in tuplas_a_buscar:
        query = Q("nested", path="atributos", query=Q("bool", must=[
                Q("term", atributos__variable=element[0]),
                Q("term", atributos__valor=element[1])
            ]))
        busquedas.append(query)
      s = Search(index="collections", doc_type="doc").query(Q("bool", must=busquedas))
      response = s.execute()
      for hit in response:
        return hit.id
    except:
        return "No se puedo pudo zippear variables y valores"