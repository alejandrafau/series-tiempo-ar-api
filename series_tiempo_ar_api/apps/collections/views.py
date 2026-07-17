import json
import re

from django.http import JsonResponse
from django.views.decorators.http import require_GET, require_POST
from django.views.decorators.csrf import csrf_exempt
from .elasticsearch_code import get_details, get_series
from .models import Collection, Concept
from .validators import GetSeriesQueryValidator


def parse_dimensiones(query_dict):
    """Convierte dimensiones[nombre]=valor en {'nombre': valor}."""
    filtros = {}
    pattern = re.compile(r'^dimensiones\[(.+)\]$')
    for key in query_dict:
        match = pattern.match(key)
        if match:
            dimension = match.group(1)
            valores = query_dict.getlist(key)
            filtros[dimension] = valores if len(valores) > 1 else valores[0]
    return filtros
from series_tiempo_ar_api.apps.api.query.pipeline import QueryPipeline
import pandas as pd
import yaml
import io
import numpy as np
from .unstack_code import (
validate_date,
validate_descri,
get_numeric,
independence_check,
divisor_valid,
dataframes_creator,
tidy_index
)

ENCODINGS = [
    "utf-8",
    "utf-8-sig",
    "ISO-8859-1",
    "latin1",
    "cp1252"
]

_JSON = {'ensure_ascii': False}


@require_GET
def get_details_view(request):
    ids_param = request.GET.get('ids')
    if not ids_param:
        return JsonResponse({'error': 'Missing required parameter: ids'}, status=400, json_dumps_params=_JSON)
    ids = [i.strip() for i in ids_param.split(',') if i.strip()]
    result = get_details(ids)
    return JsonResponse({'series': result}, json_dumps_params=_JSON)


@require_GET
def get_series_view(request):
    collection_id = request.GET.get('collection_id')
    concept_id = request.GET.get('concept_id')
    mode = request.GET.get('mode')
    filtros = parse_dimensiones(request.GET)

    validator = GetSeriesQueryValidator(collection_id, concept_id, filtros).validate()

    if validator.has_errors:
        return JsonResponse({'errors': validator.errors}, status=400, json_dumps_params=_JSON)

    result = get_series(
        collection_id, concept_id,
        validator.effective_filtros,
        mode,
    )

    if mode == 'data':
        if not result:
            response_data = {'result': []}
            if validator.warnings:
                response_data['warnings'] = validator.warnings
            return JsonResponse(response_data, json_dumps_params=_JSON)
        args = {'ids': ','.join(hit['id'] for hit in result)}
        for param in ['start_date', 'end_date', 'collapse', 'collapse_aggregation',
                      'representation_mode', 'limit', 'start']:
            val = request.GET.get(param)
            if val is not None:
                args[param] = val
        pipeline_response = QueryPipeline().run(args)
        if validator.warnings:
            data = json.loads(pipeline_response.content)
            data['warnings'] = validator.warnings
            return JsonResponse(data, json_dumps_params=_JSON)
        return pipeline_response

    response_data = {'result': result}
    if validator.warnings:
        response_data['warnings'] = validator.warnings
    return JsonResponse(response_data, json_dumps_params=_JSON)


@csrf_exempt
@require_POST
def unstack_view(request):
    """
    Enpoint que toma un csv con fechas y datos numéricos y un yaml con detalles de la
    configuración necesaria para generar archivos aptos para series de tiempo y un archivo
    compatible con collections.
    """

    # --- archivos requeridos ---
    faltantes = []
    if not request.FILES.get("csv_file"):
        faltantes.append("'csv_file'")
    if not request.FILES.get("yaml_file"):
        faltantes.append("'yaml_file'")
    if faltantes:
        return JsonResponse(
            {"error": f"Faltan los siguientes archivos en el request: {', '.join(faltantes)}."},
            status=400, json_dumps_params=_JSON,
        )

    csv_file = request.FILES["csv_file"]
    yaml_file = request.FILES["yaml_file"]

    # --- lectura CSV ---
    df = None
    for enc in ENCODINGS:
        try:
            csv_file.seek(0)
            csv_content = csv_file.read().decode(enc)
            df = pd.read_csv(io.StringIO(csv_content))
            df.columns = df.columns.str.lower()
            df = df.replace(['nan', 'NaN', 'NAN', 'null', 'NULL', ''], np.nan)
            break
        except Exception:
            continue
    if df is None:
        return JsonResponse(
            {"error": f"No se pudo leer el CSV. Probá guardarlo en alguno de estos encodings: {', '.join(ENCODINGS)}."},
            status=400, json_dumps_params=_JSON,
        )

    # --- lectura YAML ---
    try:
        config = yaml.safe_load(yaml_file.read().decode('utf-8'))
    except Exception as e:
        return JsonResponse(
            {"error": f"No se pudo parsear el YAML: {e}"},
            status=400, json_dumps_params=_JSON,
        )

    # --- claves requeridas en el YAML ---
    required_keys = ['date_col', 'descri_cols', 'div_col', 'collection_id', 'collection_name', 'concepts']
    missing_keys = [k for k in required_keys if k not in (config or {})]
    if missing_keys:
        plural = len(missing_keys) > 1
        return JsonResponse(
            {
                "error": (
                    f"El YAML no tiene {'las claves' if plural else 'la clave'} "
                    f"requerida{'s' if plural else ''}: {', '.join(missing_keys)}."
                ),
                "claves_requeridas": required_keys,
            },
            status=400, json_dumps_params=_JSON,
        )

    date_col = config['date_col']
    descri_cols = config['descri_cols']
    div_col = config['div_col']
    concepts = config['concepts']

    # --- validar estructura de cada concepto ---
    concept_required = ['id', 'name', 'num_col']
    concept_errors = []
    for i, c in enumerate(concepts):
        faltantes = [k for k in concept_required if k not in c]
        if faltantes:
            concept_errors.append(f"Concepto {i}: faltan las claves {faltantes}.")
    if concept_errors:
        return JsonResponse(
            {
                "error": "Estructura inválida en 'concepts'.",
                "detalle": concept_errors,
                "claves_requeridas_por_concepto": concept_required,
            },
            status=400, json_dumps_params=_JSON,
        )

    num_cols = [c['num_col'] for c in concepts]

    # --- columnas del YAML presentes en el CSV ---
    available = set(df.columns)
    missing = {}
    for col in ([date_col] if isinstance(date_col, str) else date_col):
        if col not in available:
            missing.setdefault('date_col', []).append(col)
    for col in descri_cols:
        if col not in available:
            missing.setdefault('descri_cols', []).append(col)
    for col in num_cols:
        if col not in available:
            missing.setdefault('concepts[num_col]', []).append(col)
    for col in ([div_col] if isinstance(div_col, str) else div_col):
        if col != 'ninguno' and col not in available:
            missing.setdefault('div_col', []).append(col)
    if missing:
        return JsonResponse(
            {
                "error": "Columnas declaradas en el YAML no encontradas en el CSV.",
                "columnas_faltantes": missing,
                "columnas_disponibles": sorted(available),
            },
            status=400, json_dumps_params=_JSON,
        )

    # --- procesamiento ---
    try:
        col_dict = {}
        col_dict = validate_date(df, date_col, col_dict)
        if col_dict.get('error'):
            return JsonResponse(
                {"error": f"Error en la columna de fecha '{date_col}': {col_dict['error']}"},
                status=400, json_dumps_params=_JSON,
            )
        col_dict = validate_descri(df, descri_cols, div_col, col_dict)
        col_dict = get_numeric(df, num_cols, col_dict)
        df_index = dataframes_creator(df, col_dict)
        return tidy_index(df_index, df, col_dict, config)
    except ValueError as e:
        return JsonResponse({"error": str(e)}, status=400, json_dumps_params=_JSON)
    except Exception as e:
        return JsonResponse(
            {"error": f"Error inesperado al procesar los archivos: {e}"},
            status=400, json_dumps_params=_JSON,
        )


@require_GET
def all_collections_view(request):
    collections = Collection.objects.values('id', 'nombre').order_by('id')
    return JsonResponse({'collections': list(collections)}, json_dumps_params=_JSON)


@require_GET
def all_concepts_view(request):
    collection_id = request.GET.get('collection_id')
    qs = Concept.objects.select_related('collection').order_by('id')
    if collection_id:
        qs = qs.filter(collection_id=collection_id)
    concepts = [
        {'id': c.id, 'nombre': c.nombre, 'collection_id': c.collection_id}
        for c in qs
    ]
    return JsonResponse({'concepts': concepts}, json_dumps_params=_JSON)


@require_GET
def get_collection_view(request):
    ids_param = request.GET.get('ids')
    if not ids_param:
        return JsonResponse({'error': 'Missing required parameter: ids'}, status=400, json_dumps_params=_JSON)
    ids = [i.strip() for i in ids_param.split(',') if i.strip()]
    collections = Collection.objects.prefetch_related('concepts').filter(id__in=ids)
    result = [
        {
            'id': col.id,
            'nombre': col.nombre,
            'descripcion': col.descripcion,
            'concepts': [
                {
                    'id': c.id,
                    'nombre': c.nombre,
                }
                for c in col.concepts.all()
            ]
        }
        for col in collections
    ]
    return JsonResponse({'collections': result}, json_dumps_params=_JSON)


@require_GET
def get_concept_view(request):
    ids_param = request.GET.get('ids')
    if not ids_param:
        return JsonResponse({'error': 'Missing required parameter: ids'}, status=400, json_dumps_params=_JSON)
    ids = [i.strip() for i in ids_param.split(',') if i.strip()]
    concepts = Concept.objects.select_related('collection').filter(id__in=ids)
    result = [
        {
            'id': c.id,
            'nombre': c.nombre,
            'descripcion': c.descripcion,
            'collection_id': c.collection_id,
            'dimensiones': c.dimensiones,
            'dimensiones_compatibles': c.dimensiones_compatibles,
        }
        for c in concepts
    ]
    return JsonResponse({'concepts': result}, json_dumps_params=_JSON)
