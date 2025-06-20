from rest_framework.viewsets import ModelViewSet

from .models import ChatConversation
from .permissions import IsAdminOrCreator
from .serializers import ChatConversationSerializer, ChatMessageSerializer


class ChatConversationViewSet(ModelViewSet):
    serializer_class = ChatConversationSerializer
    permission_classes = (IsAdminOrCreator, )

    def get_queryset(self):
        return ChatConversation.objects.all()

