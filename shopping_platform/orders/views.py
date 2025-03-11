from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Order, OrderItem
from cart.models import Cart
from products.models import Product
from users.models import User, Address
from django.utils import timezone

@login_required
def checkout(request):
    if not request.user.is_buyer:
        messages.error(request, 'Only buyers can checkout!')
        return redirect('product_list')

    cart_items = Cart.objects.filter(buyer=request.user)
    if not cart_items:
        messages.error(request, 'The shopping cart is empty, unable to checkout!')
        return redirect('view_cart')

    total_amount = sum(item.product.price * item.quantity for item in cart_items)
    if request.user.balance < total_amount:
        messages.error(request, 'Insufficient balance, please recharge!')
        return redirect('view_cart')

    addresses = request.user.addresses.all()

    if request.method == 'POST':
        address_mode = request.POST.get('address_mode')
        if address_mode not in ['single', 'multiple']:
            messages.error(request, 'Please select address mode!')
            return redirect('checkout')

        if address_mode == 'single':
            address_id = request.POST.get('delivery_address')
            if not address_id:
                messages.error(request, 'Please select or fill in the delivery address!')
                return redirect('checkout')
            delivery_address = get_object_or_404(Address, id=address_id, user=request.user).address_line1
        else:
            delivery_addresses = {}
            for item in cart_items:
                address_id = request.POST.get(f'delivery_address_{item.id}')
                if not address_id:
                    messages.error(request, f'Please select a shipping address for product {item.product.name}')
                    return redirect('checkout')
                delivery_addresses[item] = get_object_or_404(Address, id=address_id, user=request.user).address_line1

        orders = []
        for item in cart_items:
            item_total = item.product.price * item.quantity
            delivery_address = (delivery_addresses.get(item) if address_mode == 'multiple'
                              else delivery_address)

            order = Order(
                buyer=request.user,
                total_amount=item_total,
                delivery_address=delivery_address,
                status='Pending',
                payment_status='Pending Payment'
            )
            order.save()

            OrderItem.objects.create(
                order=order,
                product=item.product,
                quantity=item.quantity,
                price=item.product.price
            )
            item.product.stock -= item.quantity
            item.product.sales += item.quantity
            item.product.save()

            orders.append(order)

        request.user.balance -= total_amount
        request.user.save()

        for order in orders:
            order.payment_status = 'Paid'
            order.save()

        cart_items.delete()
        messages.success(request, 'Order created and paid successfully!')
        return redirect('order_history')

    context = {
        'cart_items': cart_items,
        'total': total_amount,
        'addresses': addresses,
    }
    return render(request, 'orders/checkout.html', context)


@login_required
def order_history(request):
    if not request.user.is_buyer:
        messages.error(request, 'Only buyer can view purchase orders history!')
        return redirect('product_list')

    orders = Order.objects.filter(buyer=request.user).order_by('-created_at')
    context = {
        'orders': orders
    }
    return render(request, 'orders/order_history.html', context)

@login_required
def seller_orders(request):
    if not request.user.is_seller:
        messages.error(request, 'Only sellers can view sale orders history!!')
        return redirect('product_list')

    products = Product.objects.filter(seller=request.user)
    order_items = OrderItem.objects.filter(product__in=products).select_related('order')
    orders = Order.objects.filter(items__in=order_items).distinct().order_by('-created_at')
    context = {
        'orders': orders
    }
    return render(request, 'orders/seller_orders.html', context)

@login_required
def ship_order(request, order_id):
    if not request.user.is_seller:
        messages.error(request, 'Only sellers can open shipping orders!')
        return redirect('product_list')

    order = get_object_or_404(Order, id=order_id)
    order_items = order.items.filter(product__seller=request.user)
    if not order_items:
        messages.error(request, 'No authority to operate this order!')
        return redirect('seller_orders')

    if order.status == 'Pending':
        order.status = 'Shipped'
        order.shipped_at = timezone.now()
        order.save()
        messages.success(request, 'Order marked as shipped!')
    else:
        messages.error(request, 'Order status cannot be updated!')
    return redirect('seller_orders')

@login_required
def request_return(request, order_id):
    if not request.user.is_buyer:
        messages.error(request, 'Only the buyer can request a return！')
        return redirect('order_history')

    order = get_object_or_404(Order, id=order_id, buyer=request.user)
    if order.status in ['Shipped', 'Delivered'] and not order.return_requested:
        order.return_requested = True
        order.status = 'Returned'
        order.save()
        messages.success(request, 'The return request has been submitted and is waiting for the seller to process!')
    else:
        messages.error(request, 'Unable to request return!')
    return redirect('order_history')

@login_required
def process_return(request, order_id):
    if not request.user.is_seller:
        messages.error(request, 'Only the seller can process returns!')
        return redirect('seller_orders')

    order = get_object_or_404(Order, id=order_id)
    order_items = order.items.filter(product__seller=request.user)
    if not order_items or not order.return_requested:
        messages.error(request, 'Not authorized to process this return request!')
        return redirect('seller_orders')

    if order.status == 'Returned' and not order.refunded_at:
        # Return the buyer's balance
        buyer = order.buyer
        buyer.balance += order.total_amount
        buyer.save()

        # Restore Inventory
        for item in order_items:
            product = item.product
            product.stock += item.quantity
            product.save()

        order.refunded_at = timezone.now()
        order.status = 'Refunded'
        order.save()
        messages.success(request, 'Refund processed!')
    else:
        messages.error(request, 'Unable to process refund!')
    return redirect('seller_orders')