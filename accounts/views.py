from django.shortcuts import render, redirect
from django.contrib import messages
from .forms import SignUpForm
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.views.decorators.http import require_http_methods
from .limits import throttle


@throttle('5/h')
@require_http_methods(['GET', 'POST'])
def signup_view(request):
    if request.method == "POST":
        form = SignUpForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Account created successfully. You can now log in.")
            return redirect("login")
    else:
        form = SignUpForm()

    return render(request, "accounts/signup.html", {"form": form})


@login_required
@throttle('5/m')
@require_http_methods(['GET', 'POST'])
def delete_account(request):
    form = AuthenticationForm(request, data={
        'username': request.user.get_username(),
        'password': request.POST.get('password', ''),
    } if request.method == 'POST' else None)
    if request.method == 'POST' and form.is_valid():
        user = request.user
        logout(request)
        user.delete()
        messages.success(request, 'Your account, watchlist, ratings and notes have been deleted.')
        return redirect('home')
    return render(request, 'accounts/delete.html', {'form': form})
