from django.http import JsonResponse
from django.views.decorators.http import require_GET
from .elasticsearch_code import get_info, get_series


@require_GET
def get_info_view(request):
    collection = request.GET.get('collection')
    if not collection:
        return JsonResponse({'error': 'Missing "collection" parameter'}, status=400)

    result = get_info(collection)
    return JsonResponse(result, safe=False)


@require_GET
def get_series_view(request):
    collection = request.GET.get('collection')
    variables = request.GET.getlist('variables')
    valores = request.GET.getlist('valores')
    modo = request.GET.get('modo')  # opcional

    if not collection or not variables or not valores:
        return JsonResponse({'error': 'Missing one or more parameters: collection, variables, valores'}, status=400)

    result = get_series(collection, variables, valores, modo)
    return JsonResponse({'result': result})