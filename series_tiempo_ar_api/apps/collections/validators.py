from .models import Collection, Concept


def _dim_id(d):
    return d['id'] if isinstance(d, dict) else d


def _dim_valores_posibles(d):
    return d.get('valores_posibles', []) if isinstance(d, dict) else []


class GetSeriesQueryValidator:

    def __init__(self, collection_id, concept_id, filtros: dict):
        self.collection_id = collection_id
        self.concept_id = concept_id
        self.filtros = dict(filtros)

        self.errors = []
        self.warnings = []
        self.effective_filtros = dict(filtros)
        self._collection = None
        self._concept = None

    @property
    def has_errors(self):
        return bool(self.errors)

    def validate(self):
        if self.collection_id:
            self._validate_collection()
            if self.has_errors:
                return self
        if self.concept_id:
            self._validate_concept()
            if self.has_errors:
                return self
        if self.filtros and self._concept:
            self._validate_dimension_names()
            if not self.has_errors:
                self._validate_dimension_values()
                if not self.has_errors:
                    self._validate_compatibility()
        return self

    def _validate_collection(self):
        try:
            self._collection = Collection.objects.get(id=self.collection_id)
        except Collection.DoesNotExist:
            available = list(Collection.objects.values_list('id', flat=True).order_by('id'))
            self.errors.append({
                'code': 'collection_not_found',
                'message': f"La colección '{self.collection_id}' no existe.",
                'colecciones_disponibles': available,
            })

    def _validate_concept(self):
        if not self.concept_id:
            return
        try:
            qs = Concept.objects.filter(id=self.concept_id)
            if self._collection:
                qs = qs.filter(collection=self._collection)
            self._concept = qs.get()
        except Concept.DoesNotExist:
            if self._collection:
                available = list(
                    Concept.objects.filter(collection=self._collection)
                    .values('id', 'nombre').order_by('id')
                )
                msg = f"El concepto '{self.concept_id}' no existe en la colección '{self.collection_id}'."
            else:
                available = list(Concept.objects.values('id', 'nombre').order_by('id'))
                msg = f"El concepto '{self.concept_id}' no existe."
            self.errors.append({
                'code': 'concept_not_found',
                'message': msg,
                'conceptos_disponibles': available,
            })

    def _validate_dimension_names(self):
        dim_ids = {_dim_id(d) for d in self._concept.dimensiones}
        invalid = [dim for dim in self.filtros if dim not in dim_ids]
        if invalid:
            self.errors.append({
                'code': 'invalid_dimensions',
                'message': (
                    f"{'La dimensión' if len(invalid) == 1 else 'Las dimensiones'} "
                    f"{invalid} no {'existe' if len(invalid) == 1 else 'existen'} "
                    f"en el concepto '{self.concept_id}'."
                ),
                'dimensiones_invalidas': invalid,
                'dimensiones_validas': sorted(dim_ids),
            })

    def _validate_dimension_values(self):
        dim_map = {_dim_id(d): d for d in self._concept.dimensiones}
        value_errors = []
        for dim, val in self.filtros.items():
            if dim not in dim_map:
                continue
            valid_vals = _dim_valores_posibles(dim_map[dim])
            if not valid_vals:
                continue
            vals_to_check = val if isinstance(val, list) else [val]
            invalid_vals = [v for v in vals_to_check if v not in valid_vals]
            if invalid_vals:
                value_errors.append({
                    'dimension': dim,
                    'valores_invalidos': invalid_vals,
                    'valores_validos': valid_vals,
                })
        if value_errors:
            self.errors.append({
                'code': 'invalid_values',
                'message': 'Algunos valores no son válidos para sus dimensiones.',
                'detalle': value_errors,
            })

    def _validate_compatibility(self):
        compat_groups = self._concept.dimensiones_compatibles
        dimensiones = list(self.filtros.keys())
        if not compat_groups or len(dimensiones) <= 1:
            return

        dim_set = set(dimensiones)
        if any(dim_set.issubset(set(group)) for group in compat_groups):
            return

        best = []
        for group in compat_groups:
            intersection = [d for d in dimensiones if d in set(group)]
            if len(intersection) > len(best):
                best = intersection

        if not best:
            best = [dimensiones[0]]

        best_set = set(best)
        self.effective_filtros = {d: v for d, v in self.filtros.items() if d in best_set}

        self.warnings.append({
            'code': 'incompatible_dimensions',
            'message': (
                f"Las dimensiones {dimensiones} no son compatibles entre sí. "
                f"Se ejecutó la búsqueda usando: {list(self.effective_filtros.keys())}."
            ),
            'dimensiones_solicitadas': dimensiones,
            'dimensiones_usadas': list(self.effective_filtros.keys()),
            'compatibilidades_disponibles': compat_groups,
        })
