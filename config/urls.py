from django.urls import path
from . import views

urlpatterns = [
    path('config/', views.configurator, name='config'),
]