import logging
from functools import reduce

from elasticsearch import Elasticsearch
from elasticsearch.helpers import parallel_bulk
from elasticsearch_dsl import Search
from elasticsearch_dsl.connections import connections
from django_datajsonar.models import Distribution
from elasticsearch_dsl import DocType, Keyword, Nested, InnerObject
from series_tiempo_ar_api.apps.management import meta_keys
from series_tiempo_ar_api.libs.datajsonar_repositories.distribution_repository import DistributionRepository
from series_tiempo_ar_api.libs.datajsonar_repositories.series_repository import SeriesRepository
from series_tiempo_ar_api.libs.indexing import strings
from series_tiempo_ar_api.libs.indexing.indexer.data_frame import get_distribution_time_index_periodicity, init_df

from .operations import process_column
from .index import tseries_index, tscol_index

logger = logging.getLogger(__name__)

class Variables(InnerObject):
    variable = Keyword()
    valor = Keyword()
    def serialize_atributos(self):
        return {
            "variable": self.variable,
            "valor": self.valor
        }

class SerieInCollection(DocType):
    id = Keyword()
    collection = Keyword()
    atributos = Nested(Variables)

    class Meta:
        index = 'collections'
        doc_type = 'doc'
    def serialize_serie(self):
        return {
            "id": self.id,
            "collection": self.collection,
            "atributos": self.atributos,
        }




class CollectionsIndexer:
    def __init__(self, index: str):
        self.elastic: Elasticsearch = connections.get_connection()
        self.index_name = index
        self.index = tscol_index(index)

    def run(self, collection_data):
        actions = self.generate_es_actions(collection_data)

        if not actions:
            return

        for success, info in parallel_bulk(self.elastic, actions):
            if not success:
                logger.warning(strings.BULK_REQUEST_ERROR, info)



    def generate_es_actions(self, collection_data):
        actions = []
        collection_id = collection_data['id']
        for id, atributos in collection_data['series_contenidas'].items():
            serie = SerieInCollection()
            serie.id = id
            serie.collection = collection_id
            serie.atributos = atributos
            serie_dict = {}
            serie_dict['_index']= self.index_name
            serie_dict['_type'] = 'doc'
            serie_dict['_source']= serie.serialize_serie()
            actions.append(serie_dict)
        return actions

    def reindex(self, collection_data):
        collection_id = collection_data['id']
        self._delete_collection_data(collection_id)
        self.run(collection_data)

    def _delete_collection_data(self, collection_id):
           collection_docs = Search(using=self.elastic,
                                 index=self.index_name).params(conflicts='proceed').filter('term', collection=collection_id)
           collection_docs.delete()