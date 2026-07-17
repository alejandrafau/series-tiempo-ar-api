import logging

from series_tiempo_ar_api.apps.collections.models import Collection, Concept

logger = logging.getLogger(__name__)


class SeriesConceptValidator:
    def validate(self, field_id, series_concept) -> list:
        """Devuelve lista de errores; lista vacía = válido."""
        errors = []

        for key in ('collection', 'concept', 'dimensions'):
            if key not in series_concept:
                errors.append(f"Missing key '{key}'")
        if errors:
            return errors

        dimensions = series_concept['dimensions']
        if not isinstance(dimensions, list):
            return ["'dimensions' must be a list"]
        for i, dim in enumerate(dimensions):
            if 'name' not in dim:
                errors.append(f"Dimension at index {i} missing 'name'")
        if errors:
            return errors

        collection_id = series_concept['collection']
        concept_id = series_concept['concept']

        try:
            Collection.objects.get(id=collection_id)
        except Collection.DoesNotExist:
            return [f"Collection '{collection_id}' not found in DB"]

        try:
            concept = Concept.objects.get(id=concept_id)
        except Concept.DoesNotExist:
            return [f"Concept '{concept_id}' not found in DB"]

        if concept.collection_id != collection_id:
            return [
                f"Concept '{concept_id}' belongs to collection '{concept.collection_id}', not '{collection_id}'"
            ]

        valid_variables = {v['id']: v.get('valores_posibles', []) for v in (concept.dimensiones or [])}

        for dim in dimensions:
            name = dim['name']
            value = dim.get('value')
            if value is None:
                continue
            if name not in valid_variables:
                errors.append(f"Dimension '{name}' not declared in concept '{concept_id}'")
                continue
            posibles = valid_variables[name]
            if posibles and value not in posibles:
                errors.append(f"Value '{value}' for dimension '{name}' not in valores_posibles")

        return errors
