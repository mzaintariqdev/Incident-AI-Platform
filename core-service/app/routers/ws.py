from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.ws import manager

router = APIRouter()


@router.websocket("/ws/tickets")
async def ticket_updates_socket(websocket: WebSocket):
    """Dashboard clients connect here to receive live ticket_created / ticket_updated events."""
    await manager.connect(websocket)
    try:
        while True:
            # we don't expect incoming messages, but need to keep the connection alive
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)
