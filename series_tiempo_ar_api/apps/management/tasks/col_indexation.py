import logging

from django.conf import settings
from django_rq import job

from django_datajsonar.models import Node
from series_tiempo_ar_api.apps.management.models import IndexCollectionTask
#from series_tiempo_ar_api.libs.indexing.catalog_reader import index_catalog
from series_tiempo_ar_api.libs.indexing.catalog_reader import process_collections
#from series_tiempo_ar_api.libs.indexing.report.report_generator import ReportGenerator

logger = logging.getLogger(__name__)


@job('collection_index')
def schedule_collection_indexing(node=None, force=False):
    if IndexCollectionTask.objects.filter(status=IndexCollectionTask.RUNNING):
        logger.info(u'Ya está corriendo una indexación')
        return
    logger.info("Se programó la tarea")
    indexing_mode = IndexCollectionTask.ALL if force else IndexCollectionTask.UPDATED_ONLY
    task = IndexCollectionTask(indexing_mode=indexing_mode)
    task.node = node
    task.save()
    read_collection(task, force=force)

    # Verificar esta funcionalidad
    if not settings.RQ_QUEUES['indexing'].get('ASYNC', True):
       task = IndexCollectionTask.objects.get(id=task.id)
       ReportGenerator(task).generate()


@job('collection_index')
def schedule_force_collection_indexing(node=None):
    schedule_collection_indexing(node, force=True)


@job('collection_index')
def read_collection(task, read_local=False, force=False):
    """Tarea raíz de indexación. Itera sobre todos los nodos indexables (federados) e
    inicia la tarea de indexación de colecciones sobre cada uno de ellos
    """
    logger.info("Se está ejecutando read_collection")
    node = task.node
    nodes = Node.objects.filter(indexable=True) if node is None else [node]
    task.status = task.RUNNING
    for node in nodes:
        logger.info(f"Corriendo indexación de colecciones para {node}")
        process_collections(node, task, read_local, force)
