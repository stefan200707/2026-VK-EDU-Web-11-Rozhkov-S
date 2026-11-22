from django.contrib import auth
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST

from .forms import LoginForm, ProfileForm, SignupForm
from .models import Profile


def is_safe_url(request, url):
    # только адреса нашего сайта — защита от open redirect
    return bool(url) and url_has_allowed_host_and_scheme(url, allowed_hosts={request.get_host()},
                                                         require_https=request.is_secure())


def get_next_url(request, fallback):
    """URL из ?next= или скрытого поля next, если он ведёт на наш сайт."""
    url = request.POST.get('next') or request.GET.get('next')
    return url if is_safe_url(request, url) else fallback


def login(request):
    if request.method == 'POST':
        form = LoginForm(request, request.POST)
        if form.is_valid():
            auth.login(request, form.user)
            return redirect(get_next_url(request, reverse('index')))
    else:
        form = LoginForm()
    next_url = request.POST.get('next') or request.GET.get('next', '')
    return render(request, 'core/login.html', {'form': form, 'next': next_url})


def signup(request):
    if request.method == 'POST':
        form = SignupForm(request.POST, request.FILES)
        if form.is_valid():
            user = form.save()
            auth.login(request, user)
            return redirect('index')
    else:
        form = SignupForm()
    return render(request, 'core/signup.html', {'form': form})


@require_POST
def logout(request):
    auth.logout(request)
    # остаёмся на той странице, где нажали «Выход»
    referer = request.META.get('HTTP_REFERER')
    return redirect(get_next_url(request, referer if is_safe_url(request, referer) else reverse('index')))


@login_required
def profile(request):
    # у пользователя из createsuperuser профиля может не быть
    user_profile, created = Profile.objects.get_or_create(user=request.user)
    if request.method == 'POST':
        form = ProfileForm(request.POST, request.FILES, instance=user_profile)
        if form.is_valid():
            form.save()
            return redirect('profile')
    else:
        form = ProfileForm(instance=user_profile)
    return render(request, 'core/profile.html', {'form': form})
