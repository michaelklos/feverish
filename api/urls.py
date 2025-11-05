from django.urls import path
from . import views, web_views

urlpatterns = [
    path('', views.fever_api, name='fever_api'),
]

# Web interface URLs (optional)
web_urlpatterns = [
    path('', web_views.index, name='index'),
    path('login/', web_views.login_view, name='login'),
    path('logout/', web_views.logout_view, name='logout'),
]
