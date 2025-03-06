from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from .models import User
from django.contrib import messages

def register(request):
    if request.method == 'POST':
        username = request.POST['username']
        email = request.POST['email']
        password = request.POST['password']
        role = request.POST['role']  # user can choose the role(buyer/seller) by themselves

        # check if the username and the email unique
        if User.objects.filter(username=username).exists():
            messages.error(request, 'Username already exists.')
            return render(request, 'users/register.html')
        if User.objects.filter(email=email).exists():
            messages.error(request, 'Email already registered.')
            return render(request, 'users/register.html')

        # create the user
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password
        )
        # choose the role
        if role == 'buyer':
            user.is_buyer = True
        elif role == 'seller':
            user.is_seller = True
        # Make sure is_admin is always False (do not allow frontend to register admins)
        user.is_admin = False
        user.save()

        # Automatically login after registration is completed
        login(request, user)
        messages.success(request, 'Successful registration！')
        return redirect('product_list')  # Turn to home page
    return render(request, 'users/register.html')

def login_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            messages.success(request, 'Login successful！')
            return redirect('product_list')  # Turn to home page
        else:
            messages.error(request, 'Wrong username or password')
    return render(request, 'users/login.html')

@login_required
def logout_view(request):
    logout(request)
    messages.success(request, 'Successfully logout！')
    return redirect('login')  # Turn to the login page