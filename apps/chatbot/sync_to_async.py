from asgiref.sync import sync_to_async
from .serializers import ChatConversationSerializer

@sync_to_async
def conversation_messages_serializer(conversation_obj):
    ret = ChatConversationSerializer(conversation_obj, context={"action_type": "retrieve"}).data
    # print(f"ret from sync_asynce: \n\n\n[[[[[[\n{ret}\n]]]]]\n\n\n")
    # print(f"Messages: {ret.get('messages')}")
    return ret.get('messages', [])
