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
    # Calculate each subtotal
    cart_items_with_subtotal = [
        {
            'item': item,
            'subtotal': item.product.price * item.quantity
        } for item in cart_items
    ]
    context = {
        'cart_items': cart_items_with_subtotal,  # include subtotals
        'total': total
    }
    return render(request, 'cart/view_cart.html', context)

@login_required
def remove_from_cart(request, cart_id):
    cart_item = get_object_or_404(Cart, id=cart_id, buyer=request.user)
    product = cart_item.product
    cart_item.delete()
    messages.success(request, f'{product.name} removed from cart!')
    return redirect('view_cart')

@login_required
def update_cart(request, cart_id):
    if request.method == 'POST':
        cart_item = get_object_or_404(Cart, id=cart_id, buyer=request.user)
        new_quantity = int(request.POST.get('quantity', 1))
        if new_quantity > 0:
            cart_item.quantity = new_quantity
            cart_item.save()
            messages.success(request, f'Cart updated for {cart_item.product.name}!')
        else:
            messages.error(request, 'Quantity must be greater than 0!')
    return redirect('view_cart')

