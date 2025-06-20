from rest_framework.routers import SimpleRouter
from .views import (
    AuthViewSet,
    ProfileViewSet,
)

auth_routers = SimpleRouter()

auth_routers.register(prefix='auth', viewset=AuthViewSet, basename='auth')
auth_routers.register(prefix='profile', viewset=ProfileViewSet, basename='profile')