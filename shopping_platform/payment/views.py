from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.conf import settings
from decimal import Decimal
import stripe
from .forms import TopUpForm

@login_required
def top_up(request):
    if request.method == 'POST':
        form = TopUpForm(request.POST)
        if form.is_valid():
            amount = form.cleaned_data['amount']
            token = request.POST.get('stripeToken')
            if not token:
                messages.error(request, 'Payment source not provided. Please try again.')
                return render(request, 'payment/top_up.html', {'form': form, 'balance': request.user.balance})

            try:
                stripe.api_key = settings.STRIPE_SECRET_KEY
                charge = stripe.Charge.create(
                    amount=int(amount * 100),
                    currency='usd',
                    description=f'Top-Up Balance for {request.user.username}',
                    source=token,
                )
                request.user.balance += Decimal(amount)
                request.user.save()
                messages.success(request, f'Successfully topped up ${amount:.2f}. New balance: ${request.user.balance:.2f}')
                return redirect('myaccount')
            except stripe.error.CardError as e:
                messages.error(request, f'Payment failed: {str(e)}')
            except Exception as e:
                messages.error(request, f'Payment error: {str(e)}')
        else:
            messages.error(request, 'Invalid amount.')
    else:
        form = TopUpForm()

    return render(request, 'payment/top_up.html', {'form': form, 'balance': request.user.balance})