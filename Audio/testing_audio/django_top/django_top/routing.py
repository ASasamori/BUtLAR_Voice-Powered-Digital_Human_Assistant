from django.urls import re_path
from butlar import consumers

websocket_urlpatterns = [
    re_path(r"ws/butlar/$", consumers.BUtlARConsumer.as_asgi()),
]
