from django.conf.urls import url
from . import views

app_name = 'collections'

urlpatterns = [
    url(r'^get_series/$', views.get_series, name='get_series'),
    url(r'^get_info/$', views.get_info, name='get_info'),
]