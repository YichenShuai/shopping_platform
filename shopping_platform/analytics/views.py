from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from orders.models import Order, OrderItem
from products.models import Product
from django.db.models import Sum

@login_required
def statistics(request):
    if not request.user.is_admin:
        messages.error(request, 'Only admins can view statistics')
        return redirect('product_list')

    total_sales = Order.objects.filter(payment_status='Paid').aggregate(total=Sum('total_amount'))['total'] or 0

    order_count = Order.objects.filter(payment_status='Paid').count()

    top_products = Product.objects.annotate(total_sold=Sum('order_items__quantity')).order_by('-total_sold')[:5]

    context = {
        'total_sales': total_sales,
        'order_count': order_count,
        'top_products': top_products
    }
    return render(request, 'analytics/statistics.html', context)