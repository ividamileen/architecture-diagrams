from sqlalchemy import Column, Integer, String, Text, Float, Boolean, DateTime, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
import enum
from .database import Base


class PlatformType(str, enum.Enum):
    WEB = "web"
    TEAMS = "teams"


class DiagramFormat(str, enum.Enum):
    PLANTUML = "plantuml"
    DRAWIO = "drawio"


class Conversation(Base):
    __tablename__ = "conversations"

    id = Column(Integer, primary_key=True, index=True)
    platform = Column(SQLEnum(PlatformType), nullable=False)
    channel_id = Column(String(255), nullable=True, index=True)
    thread_id = Column(String(255), nullable=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    messages = relationship("Message", back_populates="conversation", cascade="all, delete-orphan")
    diagrams = relationship("Diagram", back_populates="conversation", cascade="all, delete-orphan")


class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(Integer, ForeignKey("conversations.id"), nullable=False, index=True)
    content = Column(Text, nullable=False)
    user_id = Column(String(255), nullable=False)
    user_name = Column(String(255), nullable=True)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    is_technical = Column(Boolean, default=False, index=True)
    confidence_score = Column(Float, default=0.0)

    # Technical entities extracted from message
    entities = Column(Text, nullable=True)  # JSON string of extracted entities

    # Relationships
    conversation = relationship("Conversation", back_populates="messages")


class Diagram(Base):
    __tablename__ = "diagrams"

    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(Integer, ForeignKey("conversations.id"), nullable=False, index=True)
    plantuml_code = Column(Text, nullable=True)
    drawio_xml = Column(Text, nullable=True)
    png_url = Column(String(512), nullable=True)
    version = Column(Integer, default=1)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Metadata
    components_count = Column(Integer, default=0)
    relationships_count = Column(Integer, default=0)

    # Relationships
    conversation = relationship("Conversation", back_populates="diagrams")
    modifications = relationship("Modification", back_populates="diagram", cascade="all, delete-orphan")


class Modification(Base):
    __tablename__ = "modifications"

    id = Column(Integer, primary_key=True, index=True)
    diagram_id = Column(Integer, ForeignKey("diagrams.id"), nullable=False, index=True)
    request = Column(Text, nullable=False)
    applied_at = Column(DateTime(timezone=True), server_default=func.now())
    user_id = Column(String(255), nullable=True)

    # Result of modification
    success = Column(Boolean, default=True)
    error_message = Column(Text, nullable=True)

    # Relationships
    diagram = relationship("Diagram", back_populates="modifications")
