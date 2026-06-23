import logging

from elasticsearch import Elasticsearch
from elasticsearch.helpers import parallel_bulk
from elasticsearch_dsl.connections import connections
from series_tiempo_ar_api.libs.indexing import strings

from .index import tscol_index

logger = logging.getLogger(__name__)


class CollectionsIndexer:
    def __init__(self, index: str):
        self.elastic: Elasticsearch = connections.get_connection()
        self.index_name = index
        self.index = tscol_index(index)

    def reindex(self, field_data):
        sc = field_data['series_concept']
        field_id = field_data['field_id']
        dimensions = [d for d in sc.get('dimensions', []) if d.get('value') is not None]
        action = {
            '_index': self.index_name,
            '_type': 'doc',
            '_id': field_id,
            '_source': {
                'id': field_id,
                'collection': sc.get('collection'),
                'concept': sc.get('concept'),
                'dimensions': dimensions,
            }
        }
        for success, info in parallel_bulk(self.elastic, [action]):
            if not success:
                logger.warning(strings.BULK_REQUEST_ERROR, info)