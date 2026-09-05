"""POST throttles backed by shared Redis in production."""
from functools import wraps
from django.shortcuts import render
from django_ratelimit.decorators import ratelimit


def throttle(rate):
    def decorate(view):
        @ratelimit(key='ip', rate=rate, method='POST', block=False)
        @wraps(view)
        def limited(request, *args, **kwargs):
            if getattr(request, 'limited', False):
                response = render(request, '429.html', status=429)
                response['Retry-After'] = '3600' if rate.endswith('/h') else '60'
                return response
            return view(request, *args, **kwargs)
        return limited
    return decorate
