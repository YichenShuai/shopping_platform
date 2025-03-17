from django.urls import path
from . import views

urlpatterns = [
    path('', views.product_list, name='product_list'),
    path('product/<int:product_id>/', views.product_detail, name='product_detail'),
    path('create/', views.create_product, name='create_product'),
    path('product/<int:product_id>/add_review/', views.add_review, name='add_review'),
    path('manage_inventory/', views.manage_inventory, name='manage_inventory'),
    path('toggle_product/<int:product_id>/', views.toggle_product, name='toggle_product'),
    path('delete_product/<int:product_id>/', views.delete_product, name='delete_product'),
    path('update_product/<int:product_id>/', views.update_product, name='update_product'),
]