from django.urls import path
from .views import signup_view, delete_account
from django.contrib.auth import views as auth_views
from .limits import throttle

urlpatterns = [
    path("signup/", signup_view, name="signup"),
    path('login/', throttle('10/m')(auth_views.LoginView.as_view()), name='login'),
    path('password_reset/', throttle('5/h')(auth_views.PasswordResetView.as_view()), name='password_reset'),
    path('delete/', delete_account, name='delete_account'),
]
