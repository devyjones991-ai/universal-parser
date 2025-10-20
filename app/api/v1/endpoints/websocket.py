"""API эндпоинты для WebSocket соединений"""

from typing import List, Dict, Any, Optional
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, HTTPException, status, Query
from fastapi.websockets import WebSocketState
import json
import logging

from app.services.websocket_service import websocket_service, WebSocketEventType
from app.api.deps import get_current_user_optional
from app.models.user import User

router = APIRouter()
logger = logging.getLogger(__name__)


@router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    user_id: Optional[str] = Query(None, description="ID пользователя")
):
    """Основной WebSocket эндпоинт"""
    connection_id = None
    
    try:
        # Принимаем соединение
        connection_id = await websocket_service.connect(websocket, user_id)
        
        # Отправляем информацию о соединении
        await websocket.send_text(json.dumps({
            "type": "connection_established",
            "connection_id": connection_id,
            "user_id": user_id,
            "message": "WebSocket connection established"
        }))
        
        # Основной цикл обработки сообщений
        while True:
            try:
                # Получаем сообщение
                message = await websocket.receive_text()
                
                # Обрабатываем сообщение
                await websocket_service.handle_message(connection_id, message)
                
            except WebSocketDisconnect:
                logger.info(f"WebSocket disconnected: {connection_id}")
                break
            except Exception as e:
                logger.error(f"Error processing WebSocket message: {e}")
                await websocket.send_text(json.dumps({
                    "type": "error",
                    "message": f"Error processing message: {str(e)}"
                }))
    
    except Exception as e:
        logger.error(f"WebSocket connection error: {e}")
        if connection_id:
            await websocket_service.disconnect(connection_id)
    finally:
        if connection_id:
            await websocket_service.disconnect(connection_id)


@router.websocket("/ws/{room_id}")
async def websocket_room_endpoint(
    websocket: WebSocket,
    room_id: str,
    user_id: Optional[str] = Query(None, description="ID пользователя")
):
    """WebSocket эндпоинт для комнаты"""
    connection_id = None
    
    try:
        # Принимаем соединение
        connection_id = await websocket_service.connect(websocket, user_id)
        
        # Присоединяем к комнате
        await websocket_service.join_room(connection_id, room_id)
        
        # Отправляем информацию о соединении
        await websocket.send_text(json.dumps({
            "type": "connection_established",
            "connection_id": connection_id,
            "user_id": user_id,
            "room_id": room_id,
            "message": f"WebSocket connection established for room {room_id}"
        }))
        
        # Основной цикл обработки сообщений
        while True:
            try:
                # Получаем сообщение
                message = await websocket.receive_text()
                
                # Обрабатываем сообщение
                await websocket_service.handle_message(connection_id, message)
                
            except WebSocketDisconnect:
                logger.info(f"WebSocket disconnected from room {room_id}: {connection_id}")
                break
            except Exception as e:
                logger.error(f"Error processing WebSocket message in room {room_id}: {e}")
                await websocket.send_text(json.dumps({
                    "type": "error",
                    "message": f"Error processing message: {str(e)}"
                }))
    
    except Exception as e:
        logger.error(f"WebSocket room connection error: {e}")
        if connection_id:
            await websocket_service.disconnect(connection_id)
    finally:
        if connection_id:
            await websocket_service.disconnect(connection_id)


@router.get("/connections")
async def list_connections(
    current_user: User = Depends(get_current_user_optional)
):
    """Получить список активных соединений"""
    try:
        stats = await websocket_service.get_stats()
        return {
            "connections": stats["total_connections"],
            "rooms": stats["total_rooms"],
            "users": stats["total_users"],
            "event_subscriptions": stats["event_subscriptions"],
            "room_stats": stats["room_stats"]
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting connections: {e}"
        )


@router.get("/connections/{connection_id}")
async def get_connection_info(
    connection_id: str,
    current_user: User = Depends(get_current_user_optional)
):
    """Получить информацию о соединении"""
    try:
        info = await websocket_service.get_connection_info(connection_id)
        
        if not info:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Connection not found"
            )
        
        return info
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting connection info: {e}"
        )


@router.get("/rooms/{room_id}")
async def get_room_info(
    room_id: str,
    current_user: User = Depends(get_current_user_optional)
):
    """Получить информацию о комнате"""
    try:
        info = await websocket_service.get_room_info(room_id)
        
        if not info:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Room not found"
            )
        
        return info
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting room info: {e}"
        )


@router.post("/broadcast")
async def broadcast_message(
    message: Dict[str, Any],
    current_user: User = Depends(get_current_user_optional)
):
    """Отправить сообщение всем соединениям"""
    try:
        from app.services.websocket_service import WebSocketMessage
        
        # Создаем сообщение
        ws_message = WebSocketMessage(
            id=message.get("id", "broadcast"),
            type=WebSocketEventType(message.get("type", "system.message")),
            data=message.get("data", {}),
            timestamp=message.get("timestamp"),
            user_id=message.get("user_id"),
            room=message.get("room")
        )
        
        # Отправляем всем
        await websocket_service.broadcast(ws_message)
        
        return {"message": "Broadcast sent successfully"}
    
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid message type: {e}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error broadcasting message: {e}"
        )


@router.post("/rooms/{room_id}/broadcast")
async def broadcast_to_room(
    room_id: str,
    message: Dict[str, Any],
    current_user: User = Depends(get_current_user_optional)
):
    """Отправить сообщение в комнату"""
    try:
        from app.services.websocket_service import WebSocketMessage
        
        # Создаем сообщение
        ws_message = WebSocketMessage(
            id=message.get("id", "room_broadcast"),
            type=WebSocketEventType(message.get("type", "system.message")),
            data=message.get("data", {}),
            timestamp=message.get("timestamp"),
            user_id=message.get("user_id"),
            room=room_id
        )
        
        # Отправляем в комнату
        await websocket_service.send_to_room(room_id, ws_message)
        
        return {"message": f"Message sent to room {room_id}"}
    
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid message type: {e}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error broadcasting to room: {e}"
        )


@router.post("/users/{user_id}/send")
async def send_to_user(
    user_id: str,
    message: Dict[str, Any],
    current_user: User = Depends(get_current_user_optional)
):
    """Отправить сообщение пользователю"""
    try:
        from app.services.websocket_service import WebSocketMessage
        
        # Создаем сообщение
        ws_message = WebSocketMessage(
            id=message.get("id", "user_message"),
            type=WebSocketEventType(message.get("type", "system.message")),
            data=message.get("data", {}),
            timestamp=message.get("timestamp"),
            user_id=user_id,
            room=message.get("room")
        )
        
        # Отправляем пользователю
        await websocket_service.send_to_user(user_id, ws_message)
        
        return {"message": f"Message sent to user {user_id}"}
    
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid message type: {e}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error sending to user: {e}"
        )


@router.post("/events/{event_type}")
async def trigger_event(
    event_type: str,
    data: Dict[str, Any],
    user_id: Optional[str] = Query(None, description="ID пользователя"),
    room: Optional[str] = Query(None, description="ID комнаты"),
    current_user: User = Depends(get_current_user_optional)
):
    """Запустить событие"""
    try:
        # Преобразуем строку события в enum
        try:
            event_enum = WebSocketEventType(event_type)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid event type: {event_type}"
            )
        
        # Запускаем событие
        await websocket_service.broadcast_event(
            event_type=event_enum,
            data=data,
            user_id=user_id,
            room=room
        )
        
        return {
            "message": f"Event {event_type} triggered",
            "event_type": event_type,
            "user_id": user_id,
            "room": room
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error triggering event: {e}"
        )


@router.get("/events")
async def list_events(
    current_user: User = Depends(get_current_user_optional)
):
    """Получить список доступных событий"""
    try:
        events = [
            {
                "type": event.value,
                "description": event.value.replace(".", " ").title(),
                "category": event.value.split(".")[0]
            }
            for event in WebSocketEventType
        ]
        
        return {
            "events": events,
            "total": len(events)
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error listing events: {e}"
        )


@router.post("/connections/{connection_id}/subscribe")
async def subscribe_to_events(
    connection_id: str,
    events: List[str],
    current_user: User = Depends(get_current_user_optional)
):
    """Подписать соединение на события"""
    try:
        # Преобразуем строки событий в enum'ы
        event_enums = [WebSocketEventType(event) for event in events]
        
        success = await websocket_service.subscribe_to_events(connection_id, event_enums)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Connection not found"
            )
        
        return {
            "message": f"Subscribed to events: {events}",
            "events": events
        }
    
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid event type: {e}"
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error subscribing to events: {e}"
        )


@router.post("/connections/{connection_id}/unsubscribe")
async def unsubscribe_from_events(
    connection_id: str,
    events: List[str],
    current_user: User = Depends(get_current_user_optional)
):
    """Отписать соединение от событий"""
    try:
        # Преобразуем строки событий в enum'ы
        event_enums = [WebSocketEventType(event) for event in events]
        
        success = await websocket_service.unsubscribe_from_events(connection_id, event_enums)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Connection not found"
            )
        
        return {
            "message": f"Unsubscribed from events: {events}",
            "events": events
        }
    
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid event type: {e}"
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error unsubscribing from events: {e}"
        )


@router.post("/rooms/{room_id}/join")
async def join_room(
    room_id: str,
    connection_id: str,
    current_user: User = Depends(get_current_user_optional)
):
    """Присоединить соединение к комнате"""
    try:
        success = await websocket_service.join_room(connection_id, room_id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Connection not found"
            )
        
        return {
            "message": f"Joined room {room_id}",
            "room_id": room_id,
            "connection_id": connection_id
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error joining room: {e}"
        )


@router.post("/rooms/{room_id}/leave")
async def leave_room(
    room_id: str,
    connection_id: str,
    current_user: User = Depends(get_current_user_optional)
):
    """Покинуть комнату"""
    try:
        success = await websocket_service.leave_room(connection_id, room_id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Connection not found"
            )
        
        return {
            "message": f"Left room {room_id}",
            "room_id": room_id,
            "connection_id": connection_id
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error leaving room: {e}"
        )


@router.delete("/connections/{connection_id}")
async def disconnect_connection(
    connection_id: str,
    current_user: User = Depends(get_current_user_optional)
):
    """Отключить соединение"""
    try:
        await websocket_service.disconnect(connection_id)
        
        return {
            "message": f"Connection {connection_id} disconnected",
            "connection_id": connection_id
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error disconnecting: {e}"
        )


