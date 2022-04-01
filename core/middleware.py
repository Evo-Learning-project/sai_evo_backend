from channels.db import database_sync_to_async
from channels.middleware import BaseMiddleware
from django.contrib.auth.models import AnonymousUser
from django.utils import timezone
from oauth2_provider.models import AccessToken


@database_sync_to_async
def get_user(token_key):
    try:
        now = timezone.localtime(timezone.now())
        token = AccessToken.objects.get(token=token_key, expires__gt=now)
        return token.user
    except AccessToken.DoesNotExist:
        return AnonymousUser()


class TokenAuthMiddleware(BaseMiddleware):
    def __init__(self, inner):
        self.inner = inner

    async def __call__(self, scope, receive, send):
        query = dict((x.split("=") for x in scope["query_string"].decode().split("&")))
        token_key = query.get("token")
        scope["user"] = await get_user(token_key)
        return await super().__call__(scope, receive, send)
