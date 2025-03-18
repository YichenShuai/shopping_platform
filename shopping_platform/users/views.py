from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.hashers import make_password
from django.urls import reverse
from django.core.mail import send_mail
from .models import User, Address
from .forms import UserRegistrationForm, AddressForm, UserEditForm, PasswordResetRequestForm, PasswordResetForm, ChangePasswordForm
from django.contrib import messages
import random


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

    storage = messages.get_messages(request)
    for message in storage:
        if 'logout' in str(message):
            storage.used = True
    storage.used = False
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
    try:
        addresses = user.addresses.all()
    except Address.DoesNotExist:
        addresses = []
        messages.error(request, 'You do not have an address available.')

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
        elif 'change_password' in request.POST:
            password_form = ChangePasswordForm(request.POST)
            if password_form.is_valid():
                old_password = password_form.cleaned_data['old_password']
                new_password = password_form.cleaned_data['new_password']
                if user.check_password(old_password):
                    user.set_password(new_password)
                    user.save()
                    messages.success(request, 'Password changed successfully! Please log in again.')
                    logout(request)
                    return redirect('login')
                else:
                    messages.error(request, 'Old password is incorrect.')
        return redirect('myaccount')

    address_form = AddressForm()
    edit_form = UserEditForm(instance=user)
    password_form = ChangePasswordForm()
    context = {
        'user': user,
        'addresses': addresses,
        'address_form': address_form,
        'edit_form': edit_form,
        'password_form': password_form,
    }
    return render(request, 'users/myaccount.html', context)

reset_codes = {}

def password_reset_request(request):
    if request.method == 'POST':
        form = PasswordResetRequestForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            try:
                user = User.objects.get(email=email)
                verification_code = ''.join([str(random.randint(0, 9)) for _ in range(6)])
                reset_codes[email] = verification_code
                send_mail(
                    'Password Reset Verification Code',
                    f'Your verification code is: {verification_code}',
                    'from@example.com',
                    [email],
                    fail_silently=False,
                )
                messages.success(request, 'Verification code sent to your email.')
                return redirect('password_reset_confirm')
            except User.DoesNotExist:
                messages.error(request, 'No account found with this email.')
    else:
        form = PasswordResetRequestForm()
    return render(request, 'users/password_reset_request.html', {'form': form})

def password_reset_confirm(request):
    if request.method == 'POST':
        form = PasswordResetForm(request.POST)
        if form.is_valid():
            code = form.cleaned_data['code']
            new_password = form.cleaned_data['new_password']
            for email, stored_code in reset_codes.items():
                if stored_code == code:
                    user = User.objects.get(email=email)
                    user.set_password(new_password)
                    user.save()
                    del reset_codes[email]
                    messages.success(request, 'Password reset successfully!')
                    return redirect('login')
            messages.error(request, 'Invalid verification code.')
    else:
        form = PasswordResetForm()
    return render(request, 'users/password_reset_confirm.html', {'form': form})