from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from .models import FeverUser, Feed, Group, Item


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
        try:
            user = FeverUser.objects.get(email=email)
            if user.check_password(password):
                login(request, user)
                return redirect('index')
        except FeverUser.DoesNotExist:
            pass
        
        return render(request, 'login.html', {'error': 'Invalid credentials'})
    
    return render(request, 'login.html')


def logout_view(request):
    """Logout"""
    logout(request)
    return redirect('login')
