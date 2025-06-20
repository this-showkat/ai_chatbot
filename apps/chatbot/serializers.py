from rest_framework import serializers
from apps.auth.choices import UserType
from .models import ChatConversation, ChatMessage


class ChatConversationSerializer(serializers.ModelSerializer):

    class Meta:
        model = ChatConversation
        fields = '__all__'
    
    def to_representation(self, instance):
        ret = super().to_representation(instance)
        # print(f">>>Raw Context data: {self.context}, \nand view data: {self.context.get('view').get('action')} ")
        if ('view' in self.context and self.context['view'].action == 'retrieve') or ("action_type" in self.context and self.context["action_type"] == "retrieve"):
            ret['messages'] = ChatMessageSerializer(instance.chat_message_set.all(), many=True).data

        return ret
    

class ChatMessageSerializer(serializers.ModelSerializer):

    class Meta:
        model = ChatMessage
        fields = '__all__'
    
    def to_representation(self, instance):
        ret = super().to_representation(instance)
        ret["role"] = instance.role
        ret["content"] = instance.message
        return ret



