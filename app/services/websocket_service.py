"""Сервис для WebSocket соединений и real-time обновлений"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, List, Set, Any, Optional, Callable
from dataclasses import dataclass, asdict
from enum import Enum
import uuid

from fastapi import WebSocket, WebSocketDisconnect
from fastapi.websockets import WebSocketState

logger = logging.getLogger(__name__)


class WebSocketEventType(Enum):
    """Типы WebSocket событий"""
    ITEM_UPDATED = "item.updated"
    PRICE_CHANGED = "price.changed"
    NEW_ITEM = "item.created"
    ITEM_DELETED = "item.deleted"
    USER_JOINED = "user.joined"
    USER_LEFT = "user.left"
    SOCIAL_POST_CREATED = "social.post_created"
    SOCIAL_POST_LIKED = "social.post_liked"
    ACHIEVEMENT_UNLOCKED = "achievement.unlocked"
    PARSING_STARTED = "parsing.started"
    PARSING_COMPLETED = "parsing.completed"
    PARSING_FAILED = "parsing.failed"
    ANALYTICS_UPDATED = "analytics.updated"
    NOTIFICATION = "notification"
    SYSTEM_MESSAGE = "system.message"


@dataclass
class WebSocketMessage:
    """Сообщение WebSocket"""
    id: str
    type: WebSocketEventType
    data: Dict[str, Any]
    timestamp: datetime
    user_id: Optional[str] = None
    room: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Преобразовать в словарь"""
        return {
            "id": self.id,
            "type": self.type.value,
            "data": self.data,
            "timestamp": self.timestamp.isoformat(),
            "user_id": self.user_id,
            "room": self.room
        }


@dataclass
class WebSocketConnection:
    """WebSocket соединение"""
    id: str
    websocket: WebSocket
    user_id: Optional[str] = None
    rooms: Set[str] = None
    subscribed_events: Set[WebSocketEventType] = None
    connected_at: datetime = None
    last_activity: datetime = None
    
    def __post_init__(self):
        if self.rooms is None:
            self.rooms = set()
        if self.subscribed_events is None:
            self.subscribed_events = set()
        if self.connected_at is None:
            self.connected_at = datetime.utcnow()
        if self.last_activity is None:
            self.last_activity = datetime.utcnow()


class WebSocketService:
    """Сервис для управления WebSocket соединениями"""
    
    def __init__(self):
        self.connections: Dict[str, WebSocketConnection] = {}
        self.rooms: Dict[str, Set[str]] = {}  # room_id -> set of connection_ids
        self.user_connections: Dict[str, Set[str]] = {}  # user_id -> set of connection_ids
        self.event_handlers: Dict[WebSocketEventType, List[Callable]] = {}
        self.heartbeat_interval = 30  # секунды
        self.max_connections = 1000
        self.heartbeat_task = None
        
        # Запускаем heartbeat
        self.heartbeat_task = asyncio.create_task(self._heartbeat_loop())
    
    async def connect(self, websocket: WebSocket, user_id: Optional[str] = None) -> str:
        """Принять новое WebSocket соединение"""
        connection_id = str(uuid.uuid4())
        
        try:
            await websocket.accept()
            
            connection = WebSocketConnection(
                id=connection_id,
                websocket=websocket,
                user_id=user_id
            )
            
            self.connections[connection_id] = connection
            
            # Добавляем в пользовательские соединения
            if user_id:
                if user_id not in self.user_connections:
                    self.user_connections[user_id] = set()
                self.user_connections[user_id].add(connection_id)
            
            # Отправляем приветственное сообщение
            await self._send_to_connection(connection_id, WebSocketMessage(
                id=str(uuid.uuid4()),
                type=WebSocketEventType.SYSTEM_MESSAGE,
                data={"message": "Connected to Universal Parser WebSocket"},
                timestamp=datetime.utcnow(),
                user_id=user_id
            ))
            
            logger.info(f"WebSocket connected: {connection_id} (user: {user_id})")
            return connection_id
            
        except Exception as e:
            logger.error(f"Error accepting WebSocket connection: {e}")
            raise
    
    async def disconnect(self, connection_id: str):
        """Отключить WebSocket соединение"""
        if connection_id not in self.connections:
            return
        
        connection = self.connections[connection_id]
        
        # Удаляем из комнат
        for room_id in connection.rooms:
            if room_id in self.rooms:
                self.rooms[room_id].discard(connection_id)
                if not self.rooms[room_id]:
                    del self.rooms[room_id]
        
        # Удаляем из пользовательских соединений
        if connection.user_id and connection.user_id in self.user_connections:
            self.user_connections[connection.user_id].discard(connection_id)
            if not self.user_connections[connection.user_id]:
                del self.user_connections[connection.user_id]
        
        # Закрываем соединение
        try:
            if connection.websocket.client_state == WebSocketState.CONNECTED:
                await connection.websocket.close()
        except Exception as e:
            logger.error(f"Error closing WebSocket connection: {e}")
        
        # Удаляем из списка соединений
        del self.connections[connection_id]
        
        logger.info(f"WebSocket disconnected: {connection_id}")
    
    async def join_room(self, connection_id: str, room_id: str):
        """Присоединить соединение к комнате"""
        if connection_id not in self.connections:
            return False
        
        connection = self.connections[connection_id]
        connection.rooms.add(room_id)
        
        if room_id not in self.rooms:
            self.rooms[room_id] = set()
        self.rooms[room_id].add(connection_id)
        
        # Уведомляем о присоединении к комнате
        await self._send_to_connection(connection_id, WebSocketMessage(
            id=str(uuid.uuid4()),
            type=WebSocketEventType.SYSTEM_MESSAGE,
            data={"message": f"Joined room: {room_id}"},
            timestamp=datetime.utcnow(),
            user_id=connection.user_id,
            room=room_id
        ))
        
        logger.info(f"Connection {connection_id} joined room {room_id}")
        return True
    
    async def leave_room(self, connection_id: str, room_id: str):
        """Покинуть комнату"""
        if connection_id not in self.connections:
            return False
        
        connection = self.connections[connection_id]
        connection.rooms.discard(room_id)
        
        if room_id in self.rooms:
            self.rooms[room_id].discard(connection_id)
            if not self.rooms[room_id]:
                del self.rooms[room_id]
        
        # Уведомляем о покидании комнаты
        await self._send_to_connection(connection_id, WebSocketMessage(
            id=str(uuid.uuid4()),
            type=WebSocketEventType.SYSTEM_MESSAGE,
            data={"message": f"Left room: {room_id}"},
            timestamp=datetime.utcnow(),
            user_id=connection.user_id,
            room=room_id
        ))
        
        logger.info(f"Connection {connection_id} left room {room_id}")
        return True
    
    async def subscribe_to_events(self, connection_id: str, events: List[WebSocketEventType]):
        """Подписать соединение на события"""
        if connection_id not in self.connections:
            return False
        
        connection = self.connections[connection_id]
        connection.subscribed_events.update(events)
        
        # Уведомляем о подписке
        await self._send_to_connection(connection_id, WebSocketMessage(
            id=str(uuid.uuid4()),
            type=WebSocketEventType.SYSTEM_MESSAGE,
            data={"message": f"Subscribed to events: {[e.value for e in events]}"},
            timestamp=datetime.utcnow(),
            user_id=connection.user_id
        ))
        
        logger.info(f"Connection {connection_id} subscribed to events: {[e.value for e in events]}")
        return True
    
    async def unsubscribe_from_events(self, connection_id: str, events: List[WebSocketEventType]):
        """Отписать соединение от событий"""
        if connection_id not in self.connections:
            return False
        
        connection = self.connections[connection_id]
        for event in events:
            connection.subscribed_events.discard(event)
        
        # Уведомляем об отписке
        await self._send_to_connection(connection_id, WebSocketMessage(
            id=str(uuid.uuid4()),
            type=WebSocketEventType.SYSTEM_MESSAGE,
            data={"message": f"Unsubscribed from events: {[e.value for e in events]}"},
            timestamp=datetime.utcnow(),
            user_id=connection.user_id
        ))
        
        logger.info(f"Connection {connection_id} unsubscribed from events: {[e.value for e in events]}")
        return True
    
    async def send_to_connection(self, connection_id: str, message: WebSocketMessage):
        """Отправить сообщение конкретному соединению"""
        await self._send_to_connection(connection_id, message)
    
    async def send_to_user(self, user_id: str, message: WebSocketMessage):
        """Отправить сообщение всем соединениям пользователя"""
        if user_id not in self.user_connections:
            return
        
        for connection_id in self.user_connections[user_id]:
            await self._send_to_connection(connection_id, message)
    
    async def send_to_room(self, room_id: str, message: WebSocketMessage):
        """Отправить сообщение всем в комнате"""
        if room_id not in self.rooms:
            return
        
        for connection_id in self.rooms[room_id]:
            await self._send_to_connection(connection_id, message)
    
    async def broadcast(self, message: WebSocketMessage, exclude_connections: Optional[Set[str]] = None):
        """Отправить сообщение всем соединениям"""
        exclude_connections = exclude_connections or set()
        
        for connection_id in self.connections:
            if connection_id not in exclude_connections:
                await self._send_to_connection(connection_id, message)
    
    async def broadcast_event(
        self,
        event_type: WebSocketEventType,
        data: Dict[str, Any],
        user_id: Optional[str] = None,
        room: Optional[str] = None,
        exclude_connections: Optional[Set[str]] = None
    ):
        """Отправить событие всем подходящим соединениям"""
        message = WebSocketMessage(
            id=str(uuid.uuid4()),
            type=event_type,
            data=data,
            timestamp=datetime.utcnow(),
            user_id=user_id,
            room=room
        )
        
        if room:
            await self.send_to_room(room, message)
        elif user_id:
            await self.send_to_user(user_id, message)
        else:
            await self.broadcast(message, exclude_connections)
    
    async def _send_to_connection(self, connection_id: str, message: WebSocketMessage):
        """Внутренний метод для отправки сообщения"""
        if connection_id not in self.connections:
            return
        
        connection = self.connections[connection_id]
        
        # Проверяем подписку на событие
        if message.type != WebSocketEventType.SYSTEM_MESSAGE and message.type not in connection.subscribed_events:
            return
        
        try:
            if connection.websocket.client_state == WebSocketState.CONNECTED:
                await connection.websocket.send_text(json.dumps(message.to_dict()))
                connection.last_activity = datetime.utcnow()
            else:
                # Соединение закрыто, удаляем его
                await self.disconnect(connection_id)
        except Exception as e:
            logger.error(f"Error sending message to connection {connection_id}: {e}")
            await self.disconnect(connection_id)
    
    async def _heartbeat_loop(self):
        """Цикл heartbeat для проверки соединений"""
        while True:
            try:
                await asyncio.sleep(self.heartbeat_interval)
                
                # Проверяем все соединения
                disconnected_connections = []
                
                for connection_id, connection in self.connections.items():
                    try:
                        # Отправляем ping
                        if connection.websocket.client_state == WebSocketState.CONNECTED:
                            await connection.websocket.ping()
                        else:
                            disconnected_connections.append(connection_id)
                    except Exception:
                        disconnected_connections.append(connection_id)
                
                # Удаляем отключенные соединения
                for connection_id in disconnected_connections:
                    await self.disconnect(connection_id)
                
                # Логируем статистику
                active_connections = len(self.connections)
                if active_connections > 0:
                    logger.info(f"WebSocket heartbeat: {active_connections} active connections")
                
            except Exception as e:
                logger.error(f"Error in heartbeat loop: {e}")
    
    async def get_connection_info(self, connection_id: str) -> Optional[Dict[str, Any]]:
        """Получить информацию о соединении"""
        if connection_id not in self.connections:
            return None
        
        connection = self.connections[connection_id]
        return {
            "id": connection.id,
            "user_id": connection.user_id,
            "rooms": list(connection.rooms),
            "subscribed_events": [e.value for e in connection.subscribed_events],
            "connected_at": connection.connected_at.isoformat(),
            "last_activity": connection.last_activity.isoformat(),
            "is_connected": connection.websocket.client_state == WebSocketState.CONNECTED
        }
    
    async def get_room_info(self, room_id: str) -> Optional[Dict[str, Any]]:
        """Получить информацию о комнате"""
        if room_id not in self.rooms:
            return None
        
        return {
            "room_id": room_id,
            "connections_count": len(self.rooms[room_id]),
            "connections": list(self.rooms[room_id])
        }
    
    async def get_stats(self) -> Dict[str, Any]:
        """Получить статистику WebSocket сервиса"""
        total_connections = len(self.connections)
        total_rooms = len(self.rooms)
        total_users = len(self.user_connections)
        
        # Статистика по событиям
        event_stats = {}
        for connection in self.connections.values():
            for event in connection.subscribed_events:
                event_stats[event.value] = event_stats.get(event.value, 0) + 1
        
        # Статистика по комнатам
        room_stats = {
            room_id: len(connections) 
            for room_id, connections in self.rooms.items()
        }
        
        return {
            "total_connections": total_connections,
            "total_rooms": total_rooms,
            "total_users": total_users,
            "event_subscriptions": event_stats,
            "room_stats": room_stats,
            "max_connections": self.max_connections,
            "heartbeat_interval": self.heartbeat_interval
        }
    
    async def register_event_handler(
        self,
        event_type: WebSocketEventType,
        handler: Callable
    ):
        """Зарегистрировать обработчик события"""
        if event_type not in self.event_handlers:
            self.event_handlers[event_type] = []
        
        self.event_handlers[event_type].append(handler)
        logger.info(f"Registered WebSocket event handler for {event_type.value}")
    
    async def handle_message(self, connection_id: str, message: str):
        """Обработать входящее сообщение"""
        try:
            data = json.loads(message)
            message_type = data.get("type")
            
            if message_type == "ping":
                # Отвечаем на ping
                await self._send_to_connection(connection_id, WebSocketMessage(
                    id=str(uuid.uuid4()),
                    type=WebSocketEventType.SYSTEM_MESSAGE,
                    data={"message": "pong"},
                    timestamp=datetime.utcnow(),
                    user_id=self.connections[connection_id].user_id
                ))
            
            elif message_type == "subscribe":
                # Подписка на события
                events = [WebSocketEventType(e) for e in data.get("events", [])]
                await self.subscribe_to_events(connection_id, events)
            
            elif message_type == "unsubscribe":
                # Отписка от событий
                events = [WebSocketEventType(e) for e in data.get("events", [])]
                await self.unsubscribe_from_events(connection_id, events)
            
            elif message_type == "join_room":
                # Присоединение к комнате
                room_id = data.get("room_id")
                if room_id:
                    await self.join_room(connection_id, room_id)
            
            elif message_type == "leave_room":
                # Покидание комнаты
                room_id = data.get("room_id")
                if room_id:
                    await self.leave_room(connection_id, room_id)
            
            else:
                logger.warning(f"Unknown message type: {message_type}")
        
        except json.JSONDecodeError:
            logger.error(f"Invalid JSON message from connection {connection_id}")
        except Exception as e:
            logger.error(f"Error handling message from connection {connection_id}: {e}")
    
    async def cleanup(self):
        """Очистка ресурсов"""
        if self.heartbeat_task:
            self.heartbeat_task.cancel()
        
        # Закрываем все соединения
        for connection_id in list(self.connections.keys()):
            await self.disconnect(connection_id)
        
        logger.info("WebSocket service cleaned up")


# Глобальный экземпляр WebSocket сервиса
websocket_service = WebSocketService()
