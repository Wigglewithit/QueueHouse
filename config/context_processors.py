from django.conf import settings


def site_settings(request):
    return {'support_email': settings.SUPPORT_EMAIL}
