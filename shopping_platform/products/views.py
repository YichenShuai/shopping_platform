from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Product, Review
from categories.models import Category

def product_list(request):
    # Searching and filtering
    query = request.GET.get('q')
    category_id = request.GET.get('category')
    products = Product.objects.all()

    # Searching
    if query:
        products = products.filter(name__icontains=query)

    # Filter by category
    if category_id:
        products = products.filter(category_id=category_id)

    categories = Category.objects.all()  # obtain all the categories
    context = {
        'products': products,
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
    # only buyer can publish products
    if not request.user.is_seller:
        messages.error(request, 'only buyer can publish products！')
        return redirect('product_list')

    if request.method == 'POST':
        name = request.POST['name']
        description = request.POST['description']
        price = request.POST['price']
        stock = request.POST['stock']
        category_id = request.POST['category']

        # create new product
        product = Product(
            name=name,
            description=description,
            price=price,
            stock=stock,
            seller=request.user,
            category_id=category_id
        )
        product.save()
        messages.success(request, 'new product added！')
        return redirect('product_list')

    categories = Category.objects.all()
    context = {
        'categories': categories
    }
    return render(request, 'products/create_product.html', context)