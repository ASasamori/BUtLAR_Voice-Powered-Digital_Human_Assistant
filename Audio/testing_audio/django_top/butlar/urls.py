# File: butlar/urls.py
# Author: Suhani Mitra (suhanim@bu.edu), 3/27/2025

from django.urls import path
from . import views
from .views import *
from django.contrib.auth import views as auth_views    # generic view for authentication/authorization
from django.conf import settings
from django.conf.urls.static import static    # add for static files
from datetime import datetime

'''URL patterns for the butlar app.'''

urlpatterns = [
    path('', views.ButlarHome, name='home'),
    path('interface/', butlar_interface, name="butlar"),
]

urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)