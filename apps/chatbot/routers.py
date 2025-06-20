from rest_framework.routers import SimpleRouter
from .views import ChatConversationViewSet
chatbot_routers = SimpleRouter()

chatbot_routers.register(prefix="chat-conversations", viewset=ChatConversationViewSet, basename="chat_conversation")