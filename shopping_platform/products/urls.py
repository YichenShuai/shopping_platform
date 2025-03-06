from django.urls import path
from . import views

urlpatterns = [
    path('', views.product_list, name='product_list'),  # product list
    path('product/<int:product_id>/', views.product_detail, name='product_detail'),  # product details
    path('create/', views.create_product, name='create_product'),  # release product
]