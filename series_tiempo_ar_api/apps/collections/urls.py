from django.conf.urls import url
from . import views

app_name = 'collections'

urlpatterns = [
    url(r'^get_series/$', views.get_series_view, name='get_series'),
    url(r'^get_info/$', views.get_info_view, name='get_info'),
    url(r'^unstack/$', views.unstack_view, name ='unstack'),
]