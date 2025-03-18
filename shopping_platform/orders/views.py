from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.conf import settings
from .models import Order, OrderItem
from cart.models import Cart
from products.models import Product
from users.models import User, Address
from django.utils import timezone
from django.db import transaction
import stripe

stripe.api_key = settings.STRIPE_SECRET_KEY

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
    addresses = request.user.addresses.all()

    if not addresses:
        messages.error(request, 'Please add at least one address before checkout!')
        return redirect('myaccount')

    cart_items_with_subtotal = [
        {
            'item': item,
            'subtotal': item.product.price * item.quantity
        } for item in cart_items
    ]

    selected_items = request.POST.getlist('selected_items') if request.method == 'POST' else []
    address_mode = request.POST.get('address_mode', 'single') if request.method == 'POST' else 'single'
    checkout_total = 0

    if request.method == 'POST':
        print("Selected Items:", selected_items)

        selected_cart_items = cart_items.filter(id__in=selected_items)
        if not selected_cart_items:
            messages.error(request, 'Please select at least one item to checkout!')
            return render(request, 'orders/checkout.html', {
                'cart_items': cart_items_with_subtotal,
                'total': total_amount,
                'checkout_total': checkout_total,
                'addresses': addresses,
                'selected_items': selected_items,
                'address_mode': address_mode,
                'stripe_public_key': settings.STRIPE_PUBLISHABLE_KEY,
            })

        selected_cart_items_with_subtotal = [
            {
                'item': item,
                'subtotal': item.product.price * item.quantity
            } for item in selected_cart_items
        ]
        checkout_total = sum(item['subtotal'] for item in selected_cart_items_with_subtotal)

        payment_method = request.POST.get('payment_method', 'balance')
        if payment_method == 'balance' and request.user.balance < checkout_total:
            messages.error(request, 'Insufficient balance, please recharge!')
            return render(request, 'orders/checkout.html', {
                'cart_items': cart_items_with_subtotal,
                'total': total_amount,
                'checkout_total': checkout_total,
                'addresses': addresses,
                'selected_items': selected_items,
                'address_mode': address_mode,
                'stripe_public_key': settings.STRIPE_PUBLISHABLE_KEY,
            })

        if address_mode not in ['single', 'multiple']:
            messages.error(request, 'Please select address mode!')
            return render(request, 'orders/checkout.html', {
                'cart_items': cart_items_with_subtotal,
                'total': total_amount,
                'checkout_total': checkout_total,
                'addresses': addresses,
                'selected_items': selected_items,
                'address_mode': address_mode,
                'stripe_public_key': settings.STRIPE_PUBLISHABLE_KEY,
            })

        if address_mode == 'single':
            address_id = request.POST.get('delivery_address')
            if not address_id:
                messages.error(request, 'Please select or fill in the delivery address!')
                return render(request, 'orders/checkout.html', {
                    'cart_items': cart_items_with_subtotal,
                    'total': total_amount,
                    'checkout_total': checkout_total,
                    'addresses': addresses,
                    'selected_items': selected_items,
                    'address_mode': address_mode,
                    'stripe_public_key': settings.STRIPE_PUBLISHABLE_KEY,
                })
            address = get_object_or_404(Address, id=address_id, user=request.user)
            delivery_address = f"{address.address_line1}, {address.address_line2}, {address.city}, {address.state}, {address.postal_code}, {address.country}"
        else:
            delivery_addresses = {}
            for item in selected_cart_items:
                address_id = request.POST.get(f'delivery_address_{item.id}')
                if not address_id:
                    messages.error(request, f'Please select a shipping address for product {item.product.name}')
                    return render(request, 'orders/checkout.html', {
                        'cart_items': cart_items_with_subtotal,
                        'total': total_amount,
                        'checkout_total': checkout_total,
                        'addresses': addresses,
                        'selected_items': selected_items,
                        'address_mode': address_mode,
                        'stripe_public_key': settings.STRIPE_PUBLISHABLE_KEY,
                    })
                address = get_object_or_404(Address, id=address_id, user=request.user)
                delivery_addresses[item] = f"{address.address_line1}, {address.address_line2}, {address.city}, {address.state}, {address.postal_code}, {address.country}"

        with transaction.atomic():
            # Check Inventory
            for item in selected_cart_items:
                if item.product.stock < item.quantity:
                    messages.error(request, f'Insufficient stock for {item.product.name}! Only {item.product.stock} left.')
                    return redirect('view_cart')

            # Create orders
            orders = []
            for item in selected_cart_items:
                item_total = item.product.price * item.quantity
                delivery_address = (delivery_addresses.get(item) if address_mode == 'multiple' else delivery_address)

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

            if payment_method == 'balance':
                request.user.balance -= checkout_total
                request.user.save()
                for order in orders:
                    order.payment_status = 'Paid'
                    order.save()
                    seller = order.items.first().product.seller
                    seller.balance += order.total_amount
                    seller.save()
            elif payment_method == 'card':
                payment_method_id = request.POST.get('stripe_payment_method')
                try:
                    payment_intent = stripe.PaymentIntent.create(
                        amount=int(checkout_total * 100),
                        currency='usd',
                        payment_method=payment_method_id,
                        confirm=True,
                        automatic_payment_methods={
                            'enabled': True,
                            'allow_redirects': 'never'
                        }
                    )
                    if payment_intent.status == 'succeeded':
                        for order in orders:
                            order.payment_status = 'Paid'
                            order.save()
                            seller = order.items.first().product.seller
                            seller.balance += order.total_amount
                            seller.save()
                    else:
                        raise stripe.error.StripeError("Payment failed.")
                except stripe.error.StripeError as e:
                    for order in orders:
                        order.delete()
                    messages.error(request, f'Payment error: {str(e)}')
                    return redirect('view_cart')

            # Delete purchased cart items
            selected_cart_items.delete()

        messages.success(request, 'Selected items checked out and paid successfully!')
        return redirect('view_cart')

    context = {
        'cart_items': cart_items_with_subtotal,
        'total': total_amount,
        'checkout_total': checkout_total,
        'addresses': addresses,
        'selected_items': selected_items,
        'address_mode': address_mode,
        'stripe_public_key': settings.STRIPE_PUBLISHABLE_KEY,
    }
    return render(request, 'orders/checkout.html', context)


@login_required
def order_history(request):
    if not request.user.is_buyer:
        messages.error(request, 'Only buyer can view purchase orders history!')
        return redirect('product_list')

    orders = Order.objects.filter(buyer=request.user).order_by('-created_at').prefetch_related('items')
    context = {
        'orders': orders
    }
    return render(request, 'orders/order_history.html', context)

@login_required
def seller_orders(request):
    if not request.user.is_seller:
        messages.error(request, 'Only sellers can view sale orders history!!')
        return redirect('product_list')

    orders = Order.objects.filter(items__product__seller=request.user).distinct().order_by('-created_at')
    context = {
        'orders': orders,
        'balance': request.user.balance
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

        # Deduct the seller's balance
        seller = request.user
        seller.balance -= order.total_amount
        seller.save()

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