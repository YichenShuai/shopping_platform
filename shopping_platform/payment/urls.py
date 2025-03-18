from django.urls import path
from . import views

urlpatterns = [
    path('top-up/', views.top_up, name='top_up'),
]