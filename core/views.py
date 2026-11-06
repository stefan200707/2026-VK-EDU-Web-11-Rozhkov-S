from django.shortcuts import render

from .stubs import CURRENT_USER


def login(request):
    return render(request, 'core/login.html')


def signup(request):
    return render(request, 'core/signup.html')


def profile(request):
    # Только на странице профиля юзерблок показывает авторизованного пользователя
    return render(request, 'core/profile.html', {'current_user': CURRENT_USER})
