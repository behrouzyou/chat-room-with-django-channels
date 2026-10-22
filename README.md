# Django Channels Chat Room

A Django chat-room project using Django Channels and WebSockets for real-time communication.

## Features visible in the consumer
- WebSocket connections for authenticated users
- Room-based channel groups
- Message history sent when a user connects
- Online-member tracking
- Broadcast events when users join or leave a room
- Asynchronous database access through Channels helpers

## Tech stack
- Python and Django
- Django Channels
- Daphne ASGI server
- WebSockets
- SQLite development database currently present in the repository

## Run locally
Requires Python and pip. Install Django, Channels, Daphne, and any other dependencies imported by the project. Then run migrations and start the ASGI-capable development server using the project's configured entry point.

```bash
python manage.py migrate
python manage.py runserver
```

## Configuration
Review the ASGI routing and channel-layer configuration before deployment. For multi-process or production deployments, configure a shared channel layer such as Redis and use secure settings.
