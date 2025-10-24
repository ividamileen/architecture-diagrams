from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session
from typing import List
from backend.api.models import get_db
from backend.api.models.schemas import MessageCreate, MessageResponse, ConversationResponse
from backend.api.services import ConversationService, DiagramService
from backend.config import settings
import json
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/messages", tags=["messages"])


@router.post("/", response_model=MessageResponse)
async def create_message(
    message: MessageCreate,
    db: Session = Depends(get_db)
):
    """
    Create a new message and analyze it for technical content
    """
    try:
        conversation_service = ConversationService(db)
        message_response = await conversation_service.add_message(message)

        # Check if we should trigger diagram generation
        should_generate = await conversation_service.should_generate_diagram(
            message_response.conversation_id
        )

        if should_generate:
            logger.info(
                f"Triggering diagram generation for conversation {message_response.conversation_id}"
            )
            # Trigger diagram generation in background
            # In production, this should be done via a task queue
            diagram_service = DiagramService(db)
            context = await conversation_service.get_conversation_context(
                message_response.conversation_id
            )

            try:
                await diagram_service.generate_diagram(
                    message_response.conversation_id,
                    context
                )
            except Exception as e:
                logger.error(f"Error generating diagram: {e}")
                # Don't fail the message creation if diagram generation fails

        return message_response

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating message: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/conversation/{conversation_id}", response_model=List[MessageResponse])
async def get_conversation_messages(
    conversation_id: int,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """
    Get messages from a conversation
    """
    try:
        conversation_service = ConversationService(db)
        messages = await conversation_service.get_recent_messages(
            conversation_id,
            limit=limit
        )
        return [MessageResponse.model_validate(msg) for msg in messages]

    except Exception as e:
        logger.error(f"Error getting messages: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/conversation/{conversation_id}/technical", response_model=List[MessageResponse])
async def get_technical_messages(
    conversation_id: int,
    time_window_minutes: int = None,
    db: Session = Depends(get_db)
):
    """
    Get technical messages from a conversation
    """
    try:
        conversation_service = ConversationService(db)
        messages = await conversation_service.get_technical_messages(
            conversation_id,
            time_window_minutes=time_window_minutes or settings.CONVERSATION_TIME_WINDOW_MINUTES
        )
        return [MessageResponse.model_validate(msg) for msg in messages]

    except Exception as e:
        logger.error(f"Error getting technical messages: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except:
                pass


manager = ConnectionManager()


@router.websocket("/ws/{conversation_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    conversation_id: int,
    db: Session = Depends(get_db)
):
    """
    WebSocket endpoint for real-time message updates
    """
    await manager.connect(websocket)

    try:
        while True:
            # Receive message from client
            data = await websocket.receive_text()
            message_data = json.loads(data)

            # Process message
            conversation_service = ConversationService(db)
            message_create = MessageCreate(**message_data)
            message_response = await conversation_service.add_message(message_create)

            # Send response back
            response = {
                "type": "message",
                "data": message_response.model_dump(mode='json')
            }
            await manager.broadcast(json.dumps(response))

            # Check if diagram generation should be triggered
            should_generate = await conversation_service.should_generate_diagram(
                conversation_id
            )

            if should_generate:
                # Notify clients that diagram generation is starting
                await manager.broadcast(json.dumps({
                    "type": "diagram_generation_started",
                    "conversation_id": conversation_id
                }))

                # Generate diagram
                diagram_service = DiagramService(db)
                context = await conversation_service.get_conversation_context(
                    conversation_id
                )

                try:
                    diagram = await diagram_service.generate_diagram(
                        conversation_id,
                        context
                    )

                    # Notify clients that diagram is ready
                    await manager.broadcast(json.dumps({
                        "type": "diagram_generated",
                        "conversation_id": conversation_id,
                        "diagram_id": diagram.id
                    }))

                except Exception as e:
                    logger.error(f"Error generating diagram: {e}")
                    await manager.broadcast(json.dumps({
                        "type": "diagram_generation_failed",
                        "conversation_id": conversation_id,
                        "error": str(e)
                    }))

    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(websocket)
