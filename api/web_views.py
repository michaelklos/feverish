from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from .models import FeverUser, Feed, Group, Item
from .utils import refresh_feed
import hashlib


@csrf_exempt
def index(request):
    """Main reader interface"""
    # Detect Fever API requests (clients like Fiery Feeds hit the root URL with ?api)
    if 'api' in request.GET or request.POST.get('api_key'):
        from .views import fever_api
        return fever_api(request)

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
            # Ensure fever_api_key is set/synced for Fever API clients
            expected_key = hashlib.md5(f"{user.email}:{password}".encode()).hexdigest()
            if user.fever_api_key != expected_key:
                user.fever_api_key = expected_key
                user.save(update_fields=['fever_api_key'])
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
