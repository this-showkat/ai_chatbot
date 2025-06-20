import json
import httpx
from channels.generic.websocket import AsyncWebsocketConsumer
from django.conf import settings
from django.contrib.auth import get_user_model
from channels.db import database_sync_to_async
from apps.chatbot.models import ChatConversation, ChatMessage
from django.contrib.auth.models import AnonymousUser
from apps.auth.choices import UserType
from .serializers import ChatConversationSerializer
from .sync_to_async import conversation_messages_serializer

User = get_user_model()

class ChatConsumer(AsyncWebsocketConsumer):

    async def connect(self):
        self.user = self.scope.get("user", AnonymousUser())
        
        if not self.user or self.user.is_anonymous:
            await self.close()
            return
        
        await self.accept()


    async def disconnect(self, close_code):
        pass

    async def receive(self, text_data):
        data = json.loads(text_data)
        user_message = data.get("message", "")
        is_system_message = False # to detect if the message is the initial of the conversation
        conversation = None

        messages = [
            {
                "role": "user",
                "content": user_message
            }
        ]
        conversation_id = data.get("conversation_id")

        if not user_message:
            await self.send(text_data=json.dumps({"error": "No message provided"}))
            return
        
        try:
            # Get or create conversation
            if conversation_id:
                conversation = await self.get_conversation(conversation_id)
            elif self.user.user_type == UserType.USER:
                conversation = await self.create_conversation(name=user_message)
                is_system_message = True
            else:
                await self.send(text_data=json.dumps({"error": "Unknown user"}))
                return
        except ChatConversation.DoesNotExist:
            await self.send(text_data=json.dumps({"error": "Conversation not found"}))
            return
        except Exception as e:
            await self.send(text_data=json.dumps({"error": str(e)}))

        # Save user message
        if is_system_message:
            await self.save_message(conversation, sender=self.user, message=settings.AI_SYSTEM_MESSAGE, is_system_message=is_system_message)    
        await self.save_message(conversation, sender=self.user, message=user_message)
        
        messages = await conversation_messages_serializer(conversation)

        headers = {
            "Authorization": f"Bearer {settings.AI_OPENROUTER_API_KEY}",
            "Content-Type": "application/json",
            "HTTP-Referer": settings.BASE_URL,
            "X-Title": "BAIITE DeepSeek Chatbot"
        }

        payload = {
            "model": settings.AI_MODEL_NAME,
            "stream": True,
            "messages": messages
        }

        ai_response = ""

        async with httpx.AsyncClient(timeout=60) as client:
            async with client.stream("POST", settings.AI_OPENROUTER_API_URL, headers=headers, json=payload) as response:
                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        content = line.removeprefix("data: ").strip()
                        if content == "[DONE]":
                            break
                        try:
                            chunk = json.loads(content)
                            delta = chunk['choices'][0]['delta'].get('content')
                            if delta:
                                ai_response += delta
                                await self.send(text_data=json.dumps({"response": delta}))
                        except Exception as e:
                            await self.send(text_data=json.dumps({"error": str(e)}))

        # Save AI response
        ai_agent = await User.get_ai_agent()
        await self.save_message(conversation, sender=ai_agent, message=ai_response)

    @database_sync_to_async
    def get_conversation(self, conversation_id):
        return ChatConversation.objects.get(id=conversation_id)

    @database_sync_to_async
    def create_conversation(self, name="conversation Started"):
        return ChatConversation.objects.create(name=name, created_by=self.user)

    @database_sync_to_async
    def save_message(self, conversation, sender, message, is_system_message=False):
        return ChatMessage.objects.create(
            conversation=conversation,
            sent_by=sender,
            message=message,
            is_system_message=is_system_message
        )
