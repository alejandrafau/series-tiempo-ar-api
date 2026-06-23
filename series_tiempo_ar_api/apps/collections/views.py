import json

from django.http import JsonResponse
from django.views.decorators.http import require_GET, require_POST
from django.views.decorators.csrf import csrf_exempt
from .elasticsearch_code import get_info, get_series
from .models import Collection, Concept
from series_tiempo_ar_api.apps.api.query.pipeline import QueryPipeline
import pandas as pd
import yaml
import os
import io
import numpy as np
from .unstack_code import (
validate_date,
validate_descri,
get_numeric,
independence_check,
divisor_valid,
dataframes_creator,
gen_collection_meta,
tidy_index
)

ENCODINGS = [
    "utf-8",
    "utf-8-sig",
    "ISO-8859-1",
    "latin1",
    "cp1252"
]





@require_GET
def get_info_view(request):
    collection = request.GET.get('collection')
    if not collection:
        return JsonResponse({'error': 'Missing "collection" parameter'}, status=400)

    result = get_info(collection)
    return JsonResponse(result, safe=False)


@require_GET
def get_series_view(request):
    collection_id = request.GET.get('collection_id')
    concept_id = request.GET.get('concept_id')
    dimensiones = request.GET.getlist('dimensiones')
    mode = request.GET.get('mode')

    if not collection_id:
        return JsonResponse({'error': 'Missing required parameter: collection_id'}, status=400)

    # Cada valor puede ser un string simple o un JSON array para OR entre valores
    valores = []
    for v in request.GET.getlist('valores'):
        try:
            parsed = json.loads(v)
            valores.append(parsed if isinstance(parsed, list) else v)
        except (json.JSONDecodeError, ValueError):
            valores.append(v)

    result = get_series(collection_id, concept_id, dimensiones, valores, mode)

    if mode == 'data':
        if not result:
            return JsonResponse({'result': []})
        args = {'ids': ','.join(result)}
        for param in ['start_date', 'end_date', 'collapse', 'collapse_aggregation',
                      'representation_mode', 'limit', 'start']:
            val = request.GET.get(param)
            if val is not None:
                args[param] = val
        return QueryPipeline().run(args)

    return JsonResponse({'result': result})

@csrf_exempt
@require_POST
def unstack_view(request):
    """
    Enpoint que toma un csv con fechas y datos numéricos y un yaml con detalles de la
    configuración necesaria para generar archivos aptos para series de tiempo y un archivo
    compatible con collections.
    """

    csv_file = request.FILES.get("csv_file")
    yaml_file = request.FILES.get("yaml_file")

    if not csv_file or not yaml_file:
        return JsonResponse({"error": "Debes subir un archivo CSV y un archivo YAML"}, status=400)

    try:
        # --- lectura CSV ---
        for enc in ENCODINGS:
            try:
                csv_file.seek(0)
                csv_content = csv_file.read().decode(enc)
                df = pd.read_csv(io.StringIO(csv_content))
                df = df.replace(['nan', 'NaN', 'NAN', 'null', 'NULL', ''], np.nan)
                break
            except Exception:
                continue
        else:
            return JsonResponse({"error": "No se reconoció encoding del csv"}, status=400)

        # --- lectura YAML ---
        config = yaml.safe_load(yaml_file.read())

        date_col = config['date_col']
        descri_cols = config['descri_cols']
        num_cols = config['num_cols']
        div_col = config['div_col']

        col_dict = {}
        col_dict = validate_date(df, date_col, col_dict)
        col_dict = validate_descri(df, descri_cols, div_col, col_dict)
        col_dict = get_numeric(df, num_cols, col_dict)
        df_index = dataframes_creator(df, col_dict)

        # --- estructuración ZIP y envio
        return tidy_index(df_index, df, col_dict)



    except Exception as e:
        return JsonResponse({"error": str(e)}, status=400)

@require_GET
def all_collections_view(request):
    collections = Collection.objects.values('id', 'nombre').order_by('id')
    return JsonResponse({'collections': list(collections)})


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
    return JsonResponse({'concepts': concepts})


@require_GET
def get_collection_view(request):
    collection_id = request.GET.get('id')
    if not collection_id:
        return JsonResponse({'error': 'Missing required parameter: id'}, status=400)
    try:
        col = Collection.objects.prefetch_related('concepts').get(id=collection_id)
    except Collection.DoesNotExist:
        return JsonResponse({'error': f'Collection "{collection_id}" not found'}, status=404)
    return JsonResponse({
        'id': col.id,
        'nombre': col.nombre,
        'descripcion': col.descripcion,
        'concepts': [
            {
                'id': c.id,
                'nombre': c.nombre,
                'descripcion': c.descripcion,
                'variables': c.variables,
                'variables_compatibles': c.variables_compatibles,
            }
            for c in col.concepts.all()
        ]
    })


@require_GET
def get_concept_view(request):
    concept_id = request.GET.get('id')
    if not concept_id:
        return JsonResponse({'error': 'Missing required parameter: id'}, status=400)
    try:
        c = Concept.objects.select_related('collection').get(id=concept_id)
    except Concept.DoesNotExist:
        return JsonResponse({'error': f'Concept "{concept_id}" not found'}, status=404)
    return JsonResponse({
        'id': c.id,
        'nombre': c.nombre,
        'descripcion': c.descripcion,
        'collection_id': c.collection_id,
        'variables': c.variables,
        'variables_compatibles': c.variables_compatibles,
    })
