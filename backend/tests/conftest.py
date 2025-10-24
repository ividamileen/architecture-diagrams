import pytest
import asyncio
from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient

from backend.main import app
from backend.api.models.database import Base, get_db
from backend.config import settings


# Test database URL
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

# Create test engine
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db() -> Generator[Session, None, None]:
    """Create a fresh database for each test"""
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db: Session) -> Generator[TestClient, None, None]:
    """Create a test client with database override"""
    def override_get_db():
        try:
            yield db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def sample_conversation_data():
    """Sample conversation data for testing"""
    return {
        "platform": "web",
        "channel_id": "test-channel",
        "thread_id": "test-thread"
    }


@pytest.fixture
def sample_message_data():
    """Sample message data for testing"""
    return {
        "content": "We need to build an API gateway that connects to PostgreSQL database",
        "user_id": "test-user-1",
        "user_name": "Test User",
        "platform": "web"
    }


@pytest.fixture
def sample_technical_messages():
    """Sample technical messages for testing"""
    return [
        {
            "content": "We should use an API gateway for routing requests",
            "user_name": "Alice"
        },
        {
            "content": "The gateway will connect to our auth service and user service",
            "user_name": "Bob"
        },
        {
            "content": "And we'll need PostgreSQL for persistent storage",
            "user_name": "Charlie"
        },
        {
            "content": "Don't forget Redis for caching",
            "user_name": "Alice"
        }
    ]


@pytest.fixture
def sample_architecture_extraction():
    """Sample architecture extraction for testing"""
    from backend.api.models.schemas import (
        ArchitectureExtraction,
        ArchitectureEntity,
        ArchitectureRelationship
    )

    return ArchitectureExtraction(
        components=[
            ArchitectureEntity(
                type="gateway",
                name="API Gateway",
                technologies=["Nginx"]
            ),
            ArchitectureEntity(
                type="service",
                name="Auth Service",
                technologies=["Python"]
            ),
            ArchitectureEntity(
                type="database",
                name="PostgreSQL",
                technologies=["PostgreSQL"]
            ),
            ArchitectureEntity(
                type="cache",
                name="Redis",
                technologies=["Redis"]
            )
        ],
        relationships=[
            ArchitectureRelationship(
                source="API Gateway",
                target="Auth Service",
                relationship_type="api_call",
                label="authenticate"
            ),
            ArchitectureRelationship(
                source="Auth Service",
                target="PostgreSQL",
                relationship_type="data_flow",
                label="query users"
            ),
            ArchitectureRelationship(
                source="API Gateway",
                target="Redis",
                relationship_type="api_call",
                label="cache check"
            )
        ],
        context="E-commerce application with API gateway, authentication service, and database"
    )


@pytest.fixture
def mock_llm_response():
    """Mock LLM response for testing"""
    return {
        "is_technical": True,
        "confidence_score": 0.85,
        "entities": ["API Gateway", "PostgreSQL", "Redis"],
        "reasoning": "Message discusses system architecture components and their relationships"
    }
