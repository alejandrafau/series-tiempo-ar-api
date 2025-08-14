#! coding: utf-8

from elasticsearch_dsl import Index
from django.conf import settings
from .. import constants

def tscol_index(name: str) -> Index:
    index = Index (name)
    index.settings(max_result_window = settings.MAX_SERIES_VALUES)
    if not index.exists():
        index.create()
        print("Se creó el indice exitosamente")
        index.put_mapping(doc_type=settings.TS_DOC_TYPE,
                           body = constants.C_MAPPING)
        index.save()
        mapping = index.get_mapping(doc_type=settings.TS_DOC_TYPE)

        doc_properties = mapping[name]['mappings'][settings.TS_DOC_TYPE]['properties']
        if not doc_properties.get('raw_value'):
            index.put_mapping(doc_type=settings.TS_DOC_TYPE,
                              body=constants.C_MAPPING)

        return index


def tseries_index(name: str) -> Index:
    index = Index(name)

    # Fija el límite superior de valores en una respuesta. Si filtramos por serie, sería
    # la cantidad de valores máximas que puede tener una única serie temporal.
    index.settings(max_result_window=settings.MAX_SERIES_VALUES)

    if not index.exists():
        index.create()
        index.put_mapping(doc_type=settings.TS_DOC_TYPE,
                          body=constants.MAPPING)

    index.save()
    # Actualizo el mapping
    mapping = index.get_mapping(doc_type=settings.TS_DOC_TYPE)

    doc_properties = mapping[name]['mappings'][settings.TS_DOC_TYPE]['properties']
    if not doc_properties.get('raw_value'):
        index.put_mapping(doc_type=settings.TS_DOC_TYPE,
                          body=constants.MAPPING)

    return index
