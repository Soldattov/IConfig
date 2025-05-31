from django.urls import path
from . import views

app_name = 'main'
urlpatterns = [
    #path('', views.magaz, name='magaz'),
    path('', views.index, name='index'),
    path('config/', views.config, name='config'),
    path('config/save/', views.save_configuration, name='save_configuration'),
    path('config/my/', views.my_configurations, name='my_configurations'),
    path('config/<int:config_id>/', views.view_configuration, name='view_configuration'),
    path('config/<int:config_id>/delete/', views.delete_configuration, name='delete_configuration'),
    path('config/<int:config_id>/toggle-public/', views.toggle_public, name='toggle_public'),
    path('check-auth/', views.check_auth, name='check_auth'),
]