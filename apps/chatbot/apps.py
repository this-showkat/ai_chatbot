from django.apps import AppConfig


class ChatbotConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.chatbot'
    label = 'chatbot_app'
    verbose_name = 'Chatbot Module'
