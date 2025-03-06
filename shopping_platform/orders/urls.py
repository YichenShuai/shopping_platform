from django.urls import path
from . import views

urlpatterns = [
    path('checkout/', views.checkout, name='checkout'),
    path('order_history/', views.order_history, name='order_history'),
    path('seller_orders/', views.seller_orders, name='seller_orders'),
    path('ship_order/<int:order_id>/', views.ship_order, name='ship_order'),
    path('request_return/<int:order_id>/', views.request_return, name='request_return'),
    path('process_return/<int:order_id>/', views.process_return, name='process_return'),
]