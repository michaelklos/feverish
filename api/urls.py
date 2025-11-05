from django.urls import path
from . import views

urlpatterns = [
    path('', views.fever_api, name='fever_api'),
]
