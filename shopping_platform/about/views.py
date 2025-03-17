from django.shortcuts import render

def about_us(request):
    return render(request, 'about/about_us.html')

def contact_us(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        email = request.POST.get('email')
        message = request.POST.get('message')

        if name and email and message:
            try:
                from django.core.mail import send_mail
                from django.conf import settings

                subject = f'Contact Form Submission from {name}'
                message_body = f'Name: {name}\nEmail: {email}\nMessage: {message}'
                send_mail(
                    subject,
                    message_body,
                    settings.DEFAULT_FROM_EMAIL,
                    [settings.CONTACT_EMAIL],
                    fail_silently=False,
                )
                return render(request, 'about/contact_us.html', {'success': True})
            except Exception as e:
                return render(request, 'about/contact_us.html', {'error': f'Failed to send email: {str(e)}'})
        else:
            return render(request, 'about/contact_us.html', {'error': 'All fields are required.'})

    return render(request, 'about/contact_us.html')