from django.shortcuts import render


def login(request):
    return render(request, 'core/login.html')


def signup(request):
    return render(request, 'core/signup.html')


def profile(request):
    # Вход появится в ДЗ 4, пока страница показывает request.user
    return render(request, 'core/profile.html')
