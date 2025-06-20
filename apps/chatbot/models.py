from django.contrib.auth import get_user_model
from django.db import models


User = get_user_model()

class ChatConversation(models.Model):
    name = models.CharField(max_length=250)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, related_name='chat_conversation_set', related_query_name='chat_conversation', on_delete=models.PROTECT)

    def _str__(self):
        return f"{self.id}, {self.name}"


class ChatMessage(models.Model):
    conversation = models.ForeignKey(ChatConversation, related_name='chat_message_set', related_query_name='chat_message', on_delete=models.CASCADE)
    message = models.TextField()
    sent_by = models.ForeignKey(User, related_name='chat_message_set', related_query_name='chat_message', on_delete=models.CASCADE)
    sent_at = models.DateTimeField(auto_now_add=True) 
    is_system_message = models.BooleanField(default=False)

    @property
    def role(self):
        return self.sent_by.user_type if not self.is_system_message else "system"

    class Meta:
        ordering = ['id']

    def __str__(self):
        return f"Conversation: {self.conversation}, id: {self.id}, by: {self.sent_by.username}"