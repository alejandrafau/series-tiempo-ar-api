from django.conf.urls import url
from . import views

app_name = 'collections'

urlpatterns = [
    url(r'^get_series/$', views.get_series_view, name='get_series'),
    url(r'^get_info/$', views.get_info_view, name='get_info'),
    url(r'^unstack/$', views.unstack_view, name='unstack'),
    url(r'^all_collections/$', views.all_collections_view, name='all_collections'),
    url(r'^all_concepts/$', views.all_concepts_view, name='all_concepts'),
    url(r'^get_collection/$', views.get_collection_view, name='get_collection'),
    url(r'^get_concept/$', views.get_concept_view, name='get_concept'),
]