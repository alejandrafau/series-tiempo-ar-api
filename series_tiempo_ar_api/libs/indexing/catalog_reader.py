#! coding: utf-8
from __future__ import division

import json

from pydatajson import DataJson
import logging

from django_datajsonar.models import Distribution, Node
from series_tiempo_ar_api.apps.management.models import IndexDataTask
from series_tiempo_ar_api.libs.indexing.api_index_enqueue import api_index_enqueue
from series_tiempo_ar_api.libs.indexing.collection_index_enqueue import collection_index_enqueue
from series_tiempo_ar_api.libs.indexing.tasks import index_distribution
from series_tiempo_ar_api.libs.indexing.tasks import index_collection
from .strings import READ_ERROR

logger = logging.getLogger(__name__)

def index_catalog(node: Node, task, read_local=False, force=False):
    """Ejecuta el pipeline de lectura, guardado e indexado de datos
    y metadatos sobre cada distribución del catálogo especificado
    """
    logger.info("se esta corriendo indexación de catálogo")
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
    catalog = json.loads(catalog)
    collections = []
    datasets = catalog.get('dataset')
    for dataset in datasets:
        distributions = dataset.get('distribution')
        for dist in distributions:
            if dist['title'].endswith('collection_data'):
               dist['dataset']=dataset['identifier']
               collections.append(dist)

    for collection in collections:
       collection_index_enqueue(index_collection,collection,node.id,task.id)



