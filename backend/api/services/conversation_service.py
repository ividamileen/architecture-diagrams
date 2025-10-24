from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import desc
from datetime import datetime, timedelta
from backend.api.models import Conversation, Message
from backend.api.models.schemas import (
    ConversationCreate,
    MessageCreate,
    MessageResponse,
    ConversationResponse,
    PlatformType
)
from backend.ai import ConversationAnalyzer
from backend.config import settings
import json
import logging

logger = logging.getLogger(__name__)


class ConversationService:
    """Service for managing conversations and messages"""

    def __init__(self, db: Session):
        self.db = db
        self.analyzer = ConversationAnalyzer()

    async def create_conversation(
        self,
        data: ConversationCreate
    ) -> Conversation:
        """Create a new conversation"""
        conversation = Conversation(
            platform=data.platform,
            channel_id=data.channel_id,
            thread_id=data.thread_id
        )
        self.db.add(conversation)
        self.db.commit()
        self.db.refresh(conversation)
        return conversation

    async def get_conversation(
        self,
        conversation_id: int
    ) -> Optional[Conversation]:
        """Get conversation by ID"""
        return self.db.query(Conversation).filter(
            Conversation.id == conversation_id
        ).first()

    async def get_or_create_conversation(
        self,
        platform: PlatformType,
        channel_id: Optional[str] = None,
        thread_id: Optional[str] = None
    ) -> Conversation:
        """Get existing conversation or create new one"""
        # Try to find existing conversation
        query = self.db.query(Conversation).filter(
            Conversation.platform == platform
        )

        if channel_id:
            query = query.filter(Conversation.channel_id == channel_id)
        if thread_id:
            query = query.filter(Conversation.thread_id == thread_id)

        conversation = query.first()

        if not conversation:
            # Create new conversation
            conversation = Conversation(
                platform=platform,
                channel_id=channel_id,
                thread_id=thread_id
            )
            self.db.add(conversation)
            self.db.commit()
            self.db.refresh(conversation)

        return conversation

    async def add_message(
        self,
        data: MessageCreate
    ) -> MessageResponse:
        """Add a message to a conversation and analyze it"""
        # Get or create conversation
        if data.conversation_id:
            conversation = await self.get_conversation(data.conversation_id)
            if not conversation:
                raise ValueError(f"Conversation {data.conversation_id} not found")
        else:
            conversation = await self.get_or_create_conversation(
                platform=data.platform,
                channel_id=data.channel_id,
                thread_id=data.thread_id
            )

        # Get recent messages for context
        recent_messages = await self.get_recent_messages(
            conversation.id,
            limit=10
        )
        context = [msg.content for msg in recent_messages]

        # Analyze message
        analysis = await self.analyzer.analyze_message(
            message=data.content,
            context=context
        )

        # Create message
        message = Message(
            conversation_id=conversation.id,
            content=data.content,
            user_id=data.user_id,
            user_name=data.user_name,
            is_technical=analysis.is_technical,
            confidence_score=analysis.confidence_score,
            entities=json.dumps(analysis.entities)
        )

        self.db.add(message)
        self.db.commit()
        self.db.refresh(message)

        logger.info(
            f"Message added: technical={analysis.is_technical}, "
            f"confidence={analysis.confidence_score:.2f}"
        )

        return MessageResponse.model_validate(message)

    async def get_recent_messages(
        self,
        conversation_id: int,
        limit: int = 50
    ) -> List[Message]:
        """Get recent messages from a conversation"""
        return self.db.query(Message).filter(
            Message.conversation_id == conversation_id
        ).order_by(desc(Message.timestamp)).limit(limit).all()

    async def get_technical_messages(
        self,
        conversation_id: int,
        time_window_minutes: Optional[int] = None
    ) -> List[Message]:
        """Get technical messages from a conversation"""
        query = self.db.query(Message).filter(
            Message.conversation_id == conversation_id,
            Message.is_technical == True
        )

        if time_window_minutes:
            cutoff_time = datetime.utcnow() - timedelta(minutes=time_window_minutes)
            query = query.filter(Message.timestamp >= cutoff_time)

        return query.order_by(Message.timestamp).all()

    async def should_generate_diagram(
        self,
        conversation_id: int
    ) -> bool:
        """
        Determine if a diagram should be generated for this conversation
        Based on recent technical messages and confidence scores
        """
        # Get recent technical messages
        recent_technical = await self.get_technical_messages(
            conversation_id,
            time_window_minutes=settings.CONVERSATION_TIME_WINDOW_MINUTES
        )

        if not recent_technical:
            return False

        # Check if we have enough high-confidence technical messages
        high_confidence_count = sum(
            1 for msg in recent_technical
            if msg.confidence_score >= settings.TECHNICAL_CONFIDENCE_THRESHOLD
        )

        # Trigger if we have at least 3 high-confidence technical messages
        return high_confidence_count >= 3

    async def get_conversation_context(
        self,
        conversation_id: int,
        include_all: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Get conversation context for diagram generation
        Returns only technical messages by default
        """
        if include_all:
            messages = await self.get_recent_messages(
                conversation_id,
                limit=settings.CONVERSATION_CONTEXT_WINDOW_SIZE
            )
        else:
            messages = await self.get_technical_messages(
                conversation_id,
                time_window_minutes=settings.CONVERSATION_TIME_WINDOW_MINUTES
            )

        return [
            {
                "content": msg.content,
                "user_name": msg.user_name or msg.user_id,
                "timestamp": msg.timestamp.isoformat(),
                "confidence_score": msg.confidence_score
            }
            for msg in messages
        ]
