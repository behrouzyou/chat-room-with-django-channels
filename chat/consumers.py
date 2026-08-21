from channels.generic.websocket import AsyncWebsocketConsumer
import json


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
