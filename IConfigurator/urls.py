from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from config.views import component_detail

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('main.urls', namespace='main')),  # Маршруты для приложения main
    path('config/', include('config.urls')),  # Маршруты для приложения config
    path('users/', include('users.urls')),
    path('api/component/<str:component_type>/<int:component_id>/', component_detail, name='component_detail'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)