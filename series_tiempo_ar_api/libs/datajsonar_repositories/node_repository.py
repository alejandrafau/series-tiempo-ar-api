import json

from series_tiempo_ar import TimeSeriesDataJson


class NodeRepository:

    def __init__(self, node):
        self.node = node

    def read_catalog(self):
        if self.node.catalog:
            return TimeSeriesDataJson(json.loads(self.node.catalog))
        return TimeSeriesDataJson(self.node.catalog_url)
