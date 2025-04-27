"""
ASGI config for django_top project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/4.2/howto/deployment/asgi/
"""

import os

from django.core.asgi import get_asgi_application
import django
from channels.routing import get_default_application

from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from django_top.routing import websocket_urlpatterns


os.environ.setdefault("DJANGO_SETTINGS_MODULE", "django_top.settings")
django.setup()
# application = get_default_application()

application = ProtocolTypeRouter({
    "http": get_asgi_application(),  # <-- This handles normal web requests
    "websocket": AuthMiddlewareStack(
        URLRouter(websocket_urlpatterns)
    ),
})

# os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'django_top.settings')

# application = get_asgi_application()
