import jwt
from channels.db import database_sync_to_async
from channels.middleware import BaseMiddleware
from django.contrib.auth.models import AnonymousUser
from django.conf import settings
from django.contrib.auth import get_user_model
from jwt.exceptions import ExpiredSignatureError, InvalidTokenError
from urllib.parse import parse_qs


User = get_user_model()

@database_sync_to_async
def get_user(user_id):
    try:
        return User.objects.get(id=user_id)
    except User.DoesNotExist:
        return None

class TokenAuthMiddleware(BaseMiddleware):
    async def __call__(self, scope, receive, send):
        # Extract token from query string
        query_string = scope['query_string'].decode()
        query_params = parse_qs(query_string)
        token = query_params.get('token', [None])[0]

        if not token:
            await self.reject_connection(send, "Missing token")
            return
        
        try:
            payload = jwt.decode(
                token, 
                settings.SECRET_KEY, 
                algorithms=["HS256"],
                options={"verify_exp": True}
            )
            user = await get_user(payload['user_id'])
            if not user:
                await self.reject_connection(send, "Invalid user")
                return
            
            scope['user'] = user
        except ExpiredSignatureError:
            await self.reject_connection(send, "Token expired")
            return
        except InvalidTokenError:
            await self.reject_connection(send, "Invalid token")
            return
        except Exception as e:
            await self.reject_connection(send)
            return

        return await super().__call__(scope, receive, send)

    async def reject_connection(self, send, message="Authentication error"):
        await send({
            "type": "websocket.close",
            "code": 4401
        })
