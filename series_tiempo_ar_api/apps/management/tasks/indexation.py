#! coding: utf-8
import logging

from django.conf import settings
from django.utils import timezone
from django_rq import job

from django_datajsonar.models import Node
from series_tiempo_ar_api.apps.management.models import IndexDataTask
from series_tiempo_ar_api.libs.indexing.catalog_reader import index_catalog
from series_tiempo_ar_api.libs.indexing.report.report_generator import ReportGenerator

logger = logging.getLogger(__name__)


@job('api_index')
def schedule_api_indexing(node=None, force=False):
    if IndexDataTask.objects.filter(status=IndexDataTask.RUNNING):
        logger.info(u'Ya está corriendo una indexación')
        return
    logger.info("Entró a schedule api indexing")
    indexing_mode = IndexDataTask.ALL if force else IndexDataTask.UPDATED_ONLY
    task = IndexDataTask(indexing_mode=indexing_mode)
    task.node = node
    task.save()

    read_datajson(task, force=force)

    # Si se corre el comando sincrónicamete (local/testing), generar el reporte
    if not settings.RQ_QUEUES['indexing'].get('ASYNC', True):
        task = IndexDataTask.objects.get(id=task.id)
        ReportGenerator(task).generate()


@job('api_index')
def schedule_force_api_indexing(node=None):
    schedule_api_indexing(node, force=True)
    logger.info("Entró a schedule api indexing")


@job('api_index')
def read_datajson(task, read_local=False, force=False):
    """Tarea raíz de indexación. Itera sobre todos los nodos indexables (federados) e
    inicia la tarea de indexación sobre cada uno de ellos
    """
    logger.info("Entró directo a read_datajson")
    node = task.node
    nodes = Node.objects.filter(indexable=True) if node is None else [node]
    try:
        for node in nodes:
            logger.info(f"Iniciando indexación de datos para nodo '{node.catalog_id}'")
            try:
                index_catalog(node, task, read_local, force)
                logger.info(f"Finalizada indexación de datos para nodo '{node.catalog_id}'")
            except Exception as e:
                msg = f"Error indexando nodo '{node.catalog_id}': {e}"
                IndexDataTask.info(task, msg)
                logger.exception(msg)
    except Exception as e:
        msg = f"Error en read_datajson: {e}"
        IndexDataTask.info(task, msg)
        logger.exception(msg)
    finally:
        task.status = task.FINISHED
        task.finished = timezone.now()
        task.save()
        logger.info(f"Tarea IndexDataTask #{task.id} finalizada")
