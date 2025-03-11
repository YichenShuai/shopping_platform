from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from .models import User, Address
from .forms import UserRegistrationForm, AddressForm, UserEditForm
from django.contrib import messages

def register(request):
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Successful registration!')
            return redirect('product_list')
        else:
            messages.error(request, 'Registration failed. Please check the form.')
    else:
        form = UserRegistrationForm()
    return render(request, 'users/register.html', {'form': form})

def login_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            messages.success(request, 'Login successful!')
            return redirect('product_list')
        else:
            messages.error(request, 'Wrong username or password')
    return render(request, 'users/login.html')

@login_required
def logout_view(request):
    logout(request)
    messages.success(request, 'Successfully logout!')
    return redirect('product_list')

@login_required
def myaccount(request):
    user = request.user
    addresses = user.addresses.all()

    if request.method == 'POST':
        if 'delete_address' in request.POST:
            address_id = request.POST.get('address_id')
            address = get_object_or_404(Address, id=address_id, user=user)
            address.delete()
            messages.success(request, 'Address deleted successfully!')
        elif 'add_address' in request.POST:
            form = AddressForm(request.POST)
            if form.is_valid():
                address = form.save(commit=False)
                address.user = user
                address.save()
                messages.success(request, 'Address added successfully!')
        elif 'edit_profile' in request.POST:
            edit_form = UserEditForm(request.POST, instance=user)
            if edit_form.is_valid():
                edit_form.save()
                messages.success(request, 'Profile updated successfully!')
            else:
                messages.error(request, 'Update failed. Please check the form.')
        return redirect('myaccount')

    address_form = AddressForm()
    edit_form = UserEditForm(instance=user)
    context = {
        'user': user,
        'addresses': addresses,
        'address_form': address_form,
        'edit_form': edit_form,
    }
    return render(request, 'users/myaccount.html', context)