from channels.generic.websocket import AsyncWebsocketConsumer
import json
from .models import Message
from channels.db import database_sync_to_async


class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        user = self.scope["user"] # Server-trusted identity
        if not user.is_authenticated:
            await self.close()
            return

        self.room_name = self.scope["url_route"]["kwargs"]["room"]
        self.room_group_name = f"chat_{self.room_name}"
        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()

        history = await self.get_message_history(self.room_name)
        await self.send(text_data=json.dumps({"reason":"history",
                  "messages":[
                      {
                          "id": message.id,
                          "message": message.content,
                          "user_id": message.user.id,
                          "username": message.user.username,
                          "created_at": message.created_at.isoformat(),
                      } for message in history]}))

        await self.channel_layer.group_send(self.room_group_name,
                                            {"type":"chat.user_joined", "username": user.username})

    async def disconnect(self, close_code):
        await self.channel_layer.group_send(self.room_group_name,
                                            {"type":"chat.user_left", "username":self.scope["user"].username})
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    async def receive(self, text_data=None):
        data = json.loads(text_data)

        message = data["message"]
        user = self.scope["user"]
        await self.save_message(user=user, room=self.room_name, content=message)
        await self.channel_layer.group_send(self.room_group_name,
                     {"type":"chat.message", "message":message, "user_id":user.id, "username":user.username})

    async def chat_message(self, event):
        message = event["message"]
        user_id = event["user_id"]
        username = event["username"]

        await self.send(text_data=json.dumps({"reason":"message", "message":message, "user_id":user_id, "username":username}))


    async def chat_user_joined(self, event):
        await self.send(text_data=json.dumps({"reason":"user_joined", "username":event["username"]}))

    async def chat_user_left(self, event):
        await self.send(text_data=json.dumps({"reason":"user_left", "username": event["username"]}))

    @database_sync_to_async
    def save_message(self, user, room, content):
        return Message.objects.create(user=user, room=room, content=content)

    @database_sync_to_async
    def get_message_history(self, room):
        return list(Message.objects.filter(room=room).select_related("user"))
