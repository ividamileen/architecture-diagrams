from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum


class PlatformType(str, Enum):
    WEB = "web"
    TEAMS = "teams"


# Message Schemas
class MessageCreate(BaseModel):
    content: str
    user_id: str
    user_name: Optional[str] = None
    conversation_id: Optional[int] = None
    channel_id: Optional[str] = None
    thread_id: Optional[str] = None
    platform: PlatformType = PlatformType.WEB


class MessageResponse(BaseModel):
    id: int
    conversation_id: int
    content: str
    user_id: str
    user_name: Optional[str]
    timestamp: datetime
    is_technical: bool
    confidence_score: float
    entities: Optional[str]

    class Config:
        from_attributes = True


# Conversation Schemas
class ConversationCreate(BaseModel):
    platform: PlatformType
    channel_id: Optional[str] = None
    thread_id: Optional[str] = None


class ConversationResponse(BaseModel):
    id: int
    platform: PlatformType
    channel_id: Optional[str]
    thread_id: Optional[str]
    created_at: datetime
    updated_at: Optional[datetime]
    messages: List[MessageResponse] = []

    class Config:
        from_attributes = True


# Diagram Schemas
class DiagramGenerate(BaseModel):
    conversation_id: int
    force_regenerate: bool = False


class DiagramResponse(BaseModel):
    id: int
    conversation_id: int
    plantuml_code: Optional[str]
    drawio_xml: Optional[str]
    png_url: Optional[str]
    version: int
    created_at: datetime
    components_count: int
    relationships_count: int

    class Config:
        from_attributes = True


# Modification Schemas
class ModificationRequest(BaseModel):
    diagram_id: int
    request: str
    user_id: Optional[str] = None


class ModificationResponse(BaseModel):
    id: int
    diagram_id: int
    request: str
    applied_at: datetime
    success: bool
    error_message: Optional[str]
    new_diagram: Optional[DiagramResponse]

    class Config:
        from_attributes = True


# Analysis Schemas
class TechnicalAnalysis(BaseModel):
    is_technical: bool
    confidence_score: float
    entities: List[str]
    reasoning: str


class ArchitectureEntity(BaseModel):
    type: str  # service, database, api, queue, cache, etc.
    name: str
    technologies: List[str] = []


class ArchitectureRelationship(BaseModel):
    source: str
    target: str
    relationship_type: str  # api_call, data_flow, dependency, etc.
    label: Optional[str] = None


class ArchitectureExtraction(BaseModel):
    components: List[ArchitectureEntity]
    relationships: List[ArchitectureRelationship]
    context: str
