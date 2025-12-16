from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from .models import FeverUser, Feed, Group, Item
from .utils import refresh_feed


def index(request):
    """Main reader interface"""
    if not request.user.is_authenticated:
        return redirect('login')
    return render(request, 'reader.html')


def login_view(request):
    """Login page"""
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')

        # Authenticate using email instead of username
        user = authenticate(request, username=email, password=password)
        if user is not None:
            login(request, user)
            return redirect('index')

        return render(request, 'login.html', {'error': 'Invalid credentials'})

    return render(request, 'login.html')


def logout_view(request):
    """Logout"""
    logout(request)
    return redirect('login')


@login_required
def refresh_feeds_view(request):
    """Manually refresh all feeds for the current user"""
    if request.method == 'POST':
        feeds = Feed.objects.filter(user=request.user)
        for feed in feeds:
            try:
                refresh_feed(feed)
            except Exception:
                pass
    return redirect('index')
