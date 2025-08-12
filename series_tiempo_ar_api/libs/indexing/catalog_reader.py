#! coding: utf-8
from __future__ import division

import json

from pydatajson import DataJson

from django_datajsonar.models import Distribution, Node
from series_tiempo_ar_api.apps.management.models import IndexDataTask
from series_tiempo_ar_api.libs.indexing.api_index_enqueue import api_index_enqueue
from series_tiempo_ar_api.libs.indexing.collection_index_enqueue import collection_index_enqueue
from series_tiempo_ar_api.libs.indexing.tasks import index_distribution
from series_tiempo_ar_api.libs.indexing.tasks import index_collection
from .strings import READ_ERROR


def index_catalog(node: Node, task, read_local=False, force=False):
    """Ejecuta el pipeline de lectura, guardado e indexado de datos
    y metadatos sobre cada distribución del catálogo especificado
    """

    try:
        catalog = DataJson(node.catalog_url, catalog_format=node.catalog_format)
        node.catalog = json.dumps(catalog)
        node.save()
    except Exception as e:
        IndexDataTask.info(task, READ_ERROR.format(node.catalog_id, e))
        return

    distributions = Distribution.objects.filter(present=True,
                                                dataset__indexable=True,
                                                dataset__catalog__identifier=node.catalog_id)
    for distribution in distributions:
        #api_index_enqueue(index_distribution, distribution.identifier, node.id, task.id, read_local, force=force)
        index_distribution(distribution.identifier, node.id, task.id, read_local, force=force)

def process_collections(node: Node, task, read_local=False, force=False):

 catalog = node.catalog
 collections = [
     {**dist, "dataset": dataset.get("dataset_identifier")}
     for dataset in catalog.get('dataset', [])
     for dist in dataset.get('distribution', [])
     if dist.get('title', '').startswith('collection_data')
 ]
 print(collections)

 for collection in collections:
       collection_index_enqueue(index_collection,collection,node.id,task.id,read_local,force=force)



