from channels.generic.websocket import WebsocketConsumer
import json
from asgiref.sync import async_to_sync


class ChatConsumer(WebsocketConsumer):
    def connect(self):
        self.room_name = self.scope["url_route"]["kwargs"]["room"]
        self.room_group_name = f"chat_{self.room_name}"
        async_to_sync(self.channel_layer.group_add)(self.room_group_name, self.channel_name)
        self.accept()

    def disconnect(self, close_code):
        async_to_sync(self.channel_layer.group_discard)(self.room_group_name, self.channel_name)

    def receive(self, text_data=None):
        data = json.loads(text_data)

        message = data["message"]
        username = data["username"]

        async_to_sync(self.channel_layer.group_send)(self.room_group_name, {"type":"chat.message", "message":message, "username":username})

    def chat_message(self, event):
        message = event["message"]
        username = event["username"]

        self.send(text_data=json.dumps({"message":message, "username":username}))
