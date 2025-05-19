from django.urls import path
from . import views

urlpatterns = [
    path('config/', views.configurator, name='config'),
    path('api/component/<str:component_type>/<int:component_id>/', views.component_detail, name='component_detail'),
]