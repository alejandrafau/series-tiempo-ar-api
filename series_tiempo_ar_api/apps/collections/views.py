from django.http import JsonResponse
from django.views.decorators.http import require_GET, require_POST
from django.views.decorators.csrf import csrf_exempt
from .elasticsearch_code import get_info, get_series
import pandas as pd
from series_tiempo_ar_api.apps.api.views import query_view
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
    #print("entro en get series")
    collection = request.GET.get('collection')
    variables = request.GET.getlist('variables')
    valores = request.GET.getlist('valores')
    modo = request.GET.get('modo')  # opcional

    if not collection or not variables or not valores:
        return JsonResponse({'error': 'Missing one or more parameters: collection, variables, valores'}, status=400)

    result = get_series(collection, variables, valores, modo)
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

def query_view(request):
    query = QueryPipeline()
  # Formateo argumentos a lowercase, excepto ids
    ids = request.GET.get(constants.PARAM_IDS)
    args = {key: value.lower() for key, value in request.GET.items()}
    args[constants.PARAM_IDS] = ids

    response = query.run(args)
    return response
