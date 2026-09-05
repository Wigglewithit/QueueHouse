from django.contrib import admin
from django.urls import path, include
from django.views.generic import TemplateView
from accounts.limits import throttle

admin.site.login = throttle('10/m')(admin.site.login)

urlpatterns = [
    path("admin/", admin.site.urls),
    path("accounts/", include("accounts.urls")),
    path("accounts/", include("django.contrib.auth.urls")),
    path("", include("movies.urls")),
    path('privacy/', TemplateView.as_view(template_name='privacy.html'), name='privacy'),
    path('support/', TemplateView.as_view(template_name='support.html'), name='support'),
]
