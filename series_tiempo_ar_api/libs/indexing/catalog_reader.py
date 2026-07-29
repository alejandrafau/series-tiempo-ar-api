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
from series_tiempo_ar_api.libs.indexing.series_concept_validator import SeriesConceptValidator
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
        api_index_enqueue(index_distribution, distribution.identifier, node.id, task.id, read_local, force=force)
        #index_distribution(distribution.identifier, node.id, task.id, read_local, force=force)

def process_collections(node: Node, task, read_local=False, force=False):
    catalog = json.loads(node.catalog)
    validator = SeriesConceptValidator()
    for dataset in catalog.get('dataset', []):
        for dist in dataset.get('distribution', []):
            for field in dist.get('field', []):
                if field.get('specialType') != 'time_series':
                    continue
                series_concept = field.get('specialTypeDetail')
                field_id = field.get('id')
                if not series_concept or not field_id:
                    continue
                if isinstance(series_concept, str):
                    try:
                        series_concept = json.loads(series_concept)
                    except (json.JSONDecodeError, ValueError) as e:
                        logger.warning("Field '%s' skipped: specialTypeDetail no es JSON válido: %s", field_id, e)
                        continue

                errors = validator.validate(field_id, series_concept)
                if errors:
                    for err in errors:
                        logger.warning("Field '%s' skipped: %s", field_id, err)
                    continue

                collection_index_enqueue(
                    index_collection,
                    {'field_id': field_id, 'series_concept': series_concept},
                    node.id,
                    task.id,
                )

