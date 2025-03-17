from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Product, Review, ProductImage
from categories.models import Category
from django.core.paginator import Paginator
from orders.models import Order, OrderItem
from PIL import Image
import io
from django.core.files.base import ContentFile

def product_list(request):
    # Searching and filtering
    query = request.GET.get('q')
    category_id = request.GET.get('category')
    products = Product.objects.filter(is_active=True).order_by('name')

    # Searching
    if query:
        products = products.filter(name__icontains=query)

    # Filter by category
    if category_id:
        products = products.filter(category_id=category_id)

    categories = Category.objects.all()  # obtain all the categories

    # Pagination
    paginator = Paginator(products, 12)  # Display 10 products per page
    page_number = request.GET.get('page')
    products_page = paginator.get_page(page_number)

    context = {
        'products': products_page,
        'categories': categories,
        'query': query or '',
        'selected_category': category_id or ''
    }
    return render(request, 'products/product_list.html', context)

def product_detail(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    reviews = product.reviews.all()
    context = {
        'product': product,
        'reviews': reviews
    }
    return render(request, 'products/product_detail.html', context)

@login_required
def create_product(request):
    if not request.user.is_seller:
        messages.error(request, 'Only sellers can publish products!')
        return redirect('product_list')

    if request.method == 'POST':
        name = request.POST['name']
        description = request.POST['description']
        price = request.POST['price']
        stock = request.POST['stock']
        category_id = request.POST['category']
        images = request.FILES.getlist('images')

        product = Product(
            name=name,
            description=description,
            price=price,
            stock=stock,
            seller=request.user,
            category_id=category_id
        )
        product.save()


        for image in images:
            img = Image.open(image)
            img = img.convert('RGB')
            img = img.resize((800, 800), Image.LANCZOS)
            output = io.BytesIO()
            img.save(output, format='JPEG', quality=85)
            output.seek(0)
            compressed_image = ContentFile(output.read(), name=image.name.rsplit('.', 1)[0] + '.jpg')

            product_image = ProductImage(product=product, image=compressed_image)
            product_image.save()

        messages.success(request, 'New product added!')
        return redirect('manage_inventory')

    categories = Category.objects.all()
    context = {
        'categories': categories
    }
    return render(request, 'products/create_product.html', context)

@login_required
def add_review(request, product_id):
    if not request.user.is_buyer:
        messages.error(request, 'Only buyers can add reviews!')
        return redirect('product_detail', product_id=product_id)

    product = get_object_or_404(Product, id=product_id)

    # Check if the buyer has purchased the product before
    has_purchased = OrderItem.objects.filter(
        order__buyer=request.user,
        product=product
    ).exists()

    if request.method == 'POST':
        comment = request.POST['comment']
        rating = request.POST['rating']

        if not comment or not rating:
            messages.error(request, 'Comments and ratings cannot be empty!')
            return redirect('product_detail', product_id=product_id)

        review = Review(
            product=product,
            buyer=request.user,
            comment=comment,
            rating=rating
        )
        review.save()

        # Update product average rating
        product.update_rating()

        messages.success(request, 'Comment submitted successfully!')
        return redirect('product_detail', product_id=product_id)

    context = {
        'product': product,
        'has_purchased': has_purchased
    }
    return render(request, 'products/add_review.html', context)

@login_required
def manage_inventory(request):
    if not request.user.is_seller:
        messages.error(request, 'Only sellers can manage inventory!')
        return redirect('product_list')

    products = Product.objects.filter(seller=request.user)
    context = {
        'products': products
    }
    return render(request, 'products/manage_inventory.html', context)

@login_required
def toggle_product(request, product_id):
    if not request.user.is_seller:
        messages.error(request, 'Only sellers can toggle products!')
        return redirect('manage_inventory')

    product = get_object_or_404(Product, id=product_id, seller=request.user)
    product.is_active = not product.is_active
    product.save()
    messages.success(request, f'The product has already{"listed" if product.is_active else "removed"}！')
    return redirect('manage_inventory')

@login_required
def update_stock(request, product_id):
    if not request.user.is_seller:
        messages.error(request, 'Only sellers can update stock!')
        return redirect('manage_inventory')

    product = get_object_or_404(Product, id=product_id, seller=request.user)
    if request.method == 'POST':
        stock = request.POST.get('stock')
        try:
            stock = int(stock)
            if stock < 0:
                messages.error(request, 'Stock cannot be negative!')
            else:
                product.stock = stock
                product.save()
                messages.success(request, 'Stock updated successfully!')
        except ValueError:
            messages.error(request, 'Please enter a valid stock quantity!')
        return redirect('manage_inventory')

    context = {
        'product': product
    }
    return render(request, 'products/update_stock.html', context)