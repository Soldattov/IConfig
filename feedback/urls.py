# feedback/urls.py

from django.urls import path
from .views import feedback_view

urlpatterns = [
    path('', feedback_view, name='feedback'),
]
