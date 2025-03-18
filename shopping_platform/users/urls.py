from django.urls import path
from . import views

urlpatterns = [
    path('register/', views.register, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('myaccount/', views.myaccount, name='myaccount'),
    path('password_reset/', views.password_reset_request, name='password_reset'),
    path('password_reset/confirm/', views.password_reset_confirm, name='password_reset_confirm'),
]