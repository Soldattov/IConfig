from django.urls import path
from . import views

urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    path('verify_email/', views.verify_email_view, name='verify_email'),
    path('logout/', views.logout_view, name='logout'),
    path('profile/', views.profile_view, name='profile'),
    path('delete_account/', views.delete_account, name='delete_account'),
    path('verify-current-password/', views.verify_current_password, name='verify_current_password'),
    path('change-password/', views.change_password, name='change_password'),

]