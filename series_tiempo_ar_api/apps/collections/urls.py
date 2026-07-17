from django.conf.urls import url
from django.http import JsonResponse
from . import views

app_name = 'collections'

VALID_ENDPOINTS = [
    'get_series', 'get_details', 'unstack',
    'all_collections', 'all_concepts',
    'get_collection', 'get_concept',
]

def not_found_view(request, path=''):
    return JsonResponse(
        {
            'error': f'Endpoint "collections/{path}" no existe.',
            'endpoints_disponibles': [f'collections/{e}/' for e in VALID_ENDPOINTS],
        },
        status=404,
        json_dumps_params={'ensure_ascii': False},
    )

urlpatterns = [
    url(r'^get_series/$', views.get_series_view, name='get_series'),
    url(r'^get_details/$', views.get_details_view, name='get_details'),
    url(r'^unstack/$', views.unstack_view, name='unstack'),
    url(r'^all_collections/$', views.all_collections_view, name='all_collections'),
    url(r'^all_concepts/$', views.all_concepts_view, name='all_concepts'),
    url(r'^get_collection/$', views.get_collection_view, name='get_collection'),
    url(r'^get_concept/$', views.get_concept_view, name='get_concept'),
    url(r'^(?P<path>.*)$', not_found_view, name='not_found'),
]