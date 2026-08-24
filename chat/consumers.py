from channels.generic.websocket import AsyncWebsocketConsumer
import json
from .models import Message, RoomMember
from channels.db import database_sync_to_async


class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        user = self.scope["user"] # Server-trusted identity
        if not user.is_authenticated:
            await self.close()
            return

        self.user = user
        self.room_name = self.scope["url_route"]["kwargs"]["room"]
        self.room_group_name = f"chat_{self.room_name}"
        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()
        await self.add_room_member(user=self.user, room=self.room_name)
        online_users = await self.get_online_users(self.room_name)

        history = await self.get_message_history(self.room_name)
        await self.send(text_data=json.dumps({"reason":"history",
                  "messages":[
                      {
                          "id": message.id,
                          "message": message.content,
                          "user_id": message.user.id,
                          "username": message.user.username,
                          "created_at": message.created_at.isoformat(),
                      } for message in history],
                  "online_users": [
                      {
                          "id": u.user.id,
                          "username": u.user.username
                      }
                        for u in online_users
                    ]
            })
        )

        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type":"chat.user_joined",
                "username": self.user.username,
                "user_id": self.user.id
            }
        )

    async def disconnect(self, close_code):
        if not hasattr(self, "room_group_name"): return

        await self.remove_room_member(user=self.user, room=self.room_name)

        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type":"chat.user_left",
                "username": self.user.username,
                "user_id": self.user.id
            }
        )
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    async def receive(self, text_data=None):
        if not text_data: return

        try:
            data = json.loads(text_data)
        except json.JSONDecodeError:
            await self.send_error("Invalid JSON.")
            return

        if "message" not in data:
            await self.send_error("Message field is required.")
            return

        message = data["message"]
        if not isinstance(message, str):
            await self.send_error("Message must be a string.")
            return

        message = message.strip()
        if not message:
            await self.send_error("Message cannot be empty")
            return

        if len(message) > 2000:
            await self.send_error("Message is too long")
            return


        saved_message = await self.save_message(user=self.user, room=self.room_name, content=message)
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "chat.message",
                "id": saved_message.id,
                "message": saved_message.content,
                "user_id": self.user.id,
                "username": self.user.username,
                "created_at": saved_message.created_at.isoformat()
            }
        )

    async def chat_message(self, event):
        await self.send(
            text_data=json.dumps({
                "reason":"message",
                "id": event["id"],
                "message":event["message"],
                "user_id":event["user_id"],
                "username":event["username"],
                "created_at": event["created_at"]
            })
        )

    async def chat_user_joined(self, event):
        await self.send(
            text_data=json.dumps({
                "reason":"user_joined",
                "username":event["username"],
                "user_id": event["user_id"],
            })
        )

    async def chat_user_left(self, event):
        await self.send(
            text_data=json.dumps({
                "reason":"user_left",
                "username": event["username"],
                "user_id": event["user_id"],
            })
        )

    async def send_error(self, message):
        await self.send(
            text_data=json.dumps({
                "reason": "error",
                "message": message,
            })
        )

    @database_sync_to_async
    def save_message(self, user, room, content):
        return Message.objects.create(user=user, room=room, content=content)

    @database_sync_to_async
    def get_message_history(self, room):
        return list(Message.objects.filter(room=room).select_related("user").order_by("created_at"))

    @database_sync_to_async
    def add_room_member(self, user, room):
        RoomMember.objects.update_or_create(user=user, room=room, defaults={})

    @database_sync_to_async
    def remove_room_member(self, user, room):
        RoomMember.objects.filter(user=user, room=room).delete()

    @database_sync_to_async
    def get_online_users(self, room):
        return list(RoomMember.objects.filter(room=room).select_related("user").order_by("user__username"))
