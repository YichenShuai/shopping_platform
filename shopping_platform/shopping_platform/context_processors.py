from django.conf import settings

def stripe_keys(request):
    return {
        'settings': settings
    }