from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.api.models import get_db
from backend.api.models.schemas import ConversationCreate, ConversationResponse
from backend.api.services import ConversationService
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/conversations", tags=["conversations"])


@router.post("/", response_model=ConversationResponse)
async def create_conversation(
    conversation: ConversationCreate,
    db: Session = Depends(get_db)
):
    """
    Create a new conversation
    """
    try:
        conversation_service = ConversationService(db)
        new_conversation = await conversation_service.create_conversation(conversation)
        return ConversationResponse.model_validate(new_conversation)

    except Exception as e:
        logger.error(f"Error creating conversation: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/{conversation_id}", response_model=ConversationResponse)
async def get_conversation(
    conversation_id: int,
    db: Session = Depends(get_db)
):
    """
    Get a conversation by ID
    """
    try:
        conversation_service = ConversationService(db)
        conversation = await conversation_service.get_conversation(conversation_id)

        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")

        # Load messages
        messages = await conversation_service.get_recent_messages(conversation_id)

        return ConversationResponse(
            id=conversation.id,
            platform=conversation.platform,
            channel_id=conversation.channel_id,
            thread_id=conversation.thread_id,
            created_at=conversation.created_at,
            updated_at=conversation.updated_at,
            messages=[msg for msg in messages]
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting conversation: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
