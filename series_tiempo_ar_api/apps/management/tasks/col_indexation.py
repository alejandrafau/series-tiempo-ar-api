import logging

from django.utils import timezone
from django_rq import job

from django_datajsonar.models import Node
from series_tiempo_ar_api.apps.management.models import IndexCollectionTask
from series_tiempo_ar_api.libs.indexing.catalog_reader import process_collections

logger = logging.getLogger(__name__)


@job('collection_index')
def schedule_collection_indexing(node=None, force=False):
    if IndexCollectionTask.objects.filter(status=IndexCollectionTask.RUNNING):
        logger.info('Ya está corriendo una indexación de colecciones')
        return
    indexing_mode = IndexCollectionTask.ALL if force else IndexCollectionTask.UPDATED_ONLY
    task = IndexCollectionTask(indexing_mode=indexing_mode)
    task.node = node
    task.save()
    logger.info(f"Tarea IndexCollectionTask #{task.id} programada (mode={indexing_mode})")
    read_collection(task, force=force)


@job('collection_index')
def schedule_force_collection_indexing(node=None):
    schedule_collection_indexing(node, force=True)


@job('collection_index')
def read_collection(task, read_local=False, force=False):
    """Itera sobre todos los nodos indexables e inicia la indexación de colecciones."""
    logger.info(f"Iniciando read_collection para tarea #{task.id}")
    node = task.node
    nodes = Node.objects.filter(indexable=True) if node is None else [node]
    try:
        for node in nodes:
            logger.info(f"Iniciando indexación de colecciones para nodo '{node.catalog_id}'")
            try:
                process_collections(node, task, read_local, force)
                logger.info(f"Finalizada indexación de colecciones para nodo '{node.catalog_id}'")
            except Exception as e:
                msg = f"Error procesando colecciones del nodo '{node.catalog_id}': {e}"
                IndexCollectionTask.info(task, msg)
                logger.exception(msg)
    except Exception as e:
        msg = f"Error en read_collection: {e}"
        IndexCollectionTask.info(task, msg)
        logger.exception(msg)
    finally:
        task.status = task.FINISHED
        task.finished = timezone.now()
        task.save()
        logger.info(f"Tarea IndexCollectionTask #{task.id} finalizada")
