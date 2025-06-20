import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'src.settings')
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter

from apps.chatbot.middleware import TokenAuthMiddleware
from apps.chatbot.routing import websocket_urlpatterns


application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": TokenAuthMiddleware(
        URLRouter(websocket_urlpatterns)
    ),
})