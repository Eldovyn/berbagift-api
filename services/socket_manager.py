import socketio
import asyncio

sio = socketio.AsyncServer(
    async_mode='asgi',
    cors_allowed_origins='*',
    logger=False,
    engineio_logger=False
)

_event_loop: asyncio.AbstractEventLoop | None = None


def get_sio():
    return sio


def emit_threadsafe(event: str, data: dict) -> None:
    """Emit a Socket.IO event safely from any thread."""
    if _event_loop is not None and _event_loop.is_running():
        asyncio.run_coroutine_threadsafe(sio.emit(event, data), _event_loop)
    elif _event_loop is not None:
        # Event loop exists but not running — schedule on it anyway
        asyncio.run_coroutine_threadsafe(sio.emit(event, data), _event_loop)
    else:
        # No event loop yet: no clients connected, nothing to emit to
        pass


def create_socket_app(app):
    """Wrap a FastAPI/ASGI app with Socket.IO."""
    return socketio.ASGIApp(sio, other_asgi_app=app)


@sio.event
async def connect(sid, environ):
    global _event_loop
    _event_loop = asyncio.get_running_loop()
    print(f"🔌 Socket connected: {sid}")


@sio.event
async def disconnect(sid):
    print(f"🔌 Socket disconnected: {sid}")
