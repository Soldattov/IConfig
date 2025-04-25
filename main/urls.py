from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='home'),
    #path('components/', views.component_list, name='component_list'),  # Новый маршрут
]