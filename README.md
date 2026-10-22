# Django Channels Chat Room

A Django chat-room project using Django Channels and WebSockets for real-time communication.

## Features visible in the consumer
- WebSocket connections restricted to authenticated users
- Room-based channel groups
- Message history sent when a user connects
- Online-member tracking
- Broadcast events when users join or leave a room
- Asynchronous database access through Channels helpers

## Stack
- Python and Django
- Django Channels
- Daphne ASGI server
- WebSockets

## Run locally
Install Django, Channels, Daphne, and the other dependencies imported by the project. Then run migrations and start the development server:

```bash
python manage.py migrate
python manage.py runserver
```

## Deployment
Review ASGI routing and channel-layer configuration. For multi-process or production deployments, configure a shared channel layer such as Redis and use secure Django settings.
