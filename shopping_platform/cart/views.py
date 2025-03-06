from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Cart
from products.models import Product

@login_required
def add_to_cart(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    if product.stock > 0:
        cart_item, created = Cart.objects.get_or_create(buyer=request.user, product=product)
        if not created:
            cart_item.quantity += 1
            cart_item.save()
        messages.success(request, f'{product.name} successfully added to cart！')
    else:
        messages.error(request, 'Out of stock！')
    return redirect('product_list')

@login_required
def view_cart(request):
    cart_items = Cart.objects.filter(buyer=request.user)
    total = sum(item.product.price * item.quantity for item in cart_items)
    context = {
        'cart_items': cart_items,
        'total': total
    }
    return render(request, 'cart/view_cart.html', context)