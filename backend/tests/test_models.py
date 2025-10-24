import pytest
from backend.api.models import Conversation, Message, Diagram, Modification
from backend.api.models.schemas import PlatformType


@pytest.mark.unit
class TestConversationModel:
    """Test cases for Conversation model"""

    def test_create_conversation(self, db):
        """Test creating a conversation"""
        conversation = Conversation(
            platform=PlatformType.WEB,
            channel_id="test-channel",
            thread_id="test-thread"
        )
        db.add(conversation)
        db.commit()
        db.refresh(conversation)

        assert conversation.id is not None
        assert conversation.platform == PlatformType.WEB
        assert conversation.channel_id == "test-channel"
        assert conversation.created_at is not None

    def test_conversation_relationships(self, db):
        """Test conversation relationships"""
        conversation = Conversation(platform=PlatformType.WEB)
        db.add(conversation)
        db.commit()

        # Add message
        message = Message(
            conversation_id=conversation.id,
            content="Test message",
            user_id="user1"
        )
        db.add(message)
        db.commit()

        # Refresh conversation
        db.refresh(conversation)

        assert len(conversation.messages) == 1
        assert conversation.messages[0].content == "Test message"


@pytest.mark.unit
class TestMessageModel:
    """Test cases for Message model"""

    def test_create_message(self, db):
        """Test creating a message"""
        # Create conversation first
        conversation = Conversation(platform=PlatformType.WEB)
        db.add(conversation)
        db.commit()

        # Create message
        message = Message(
            conversation_id=conversation.id,
            content="Test message",
            user_id="user1",
            user_name="Test User",
            is_technical=True,
            confidence_score=0.85
        )
        db.add(message)
        db.commit()
        db.refresh(message)

        assert message.id is not None
        assert message.content == "Test message"
        assert message.is_technical is True
        assert message.confidence_score == 0.85
        assert message.timestamp is not None

    def test_message_conversation_relationship(self, db):
        """Test message-conversation relationship"""
        conversation = Conversation(platform=PlatformType.WEB)
        db.add(conversation)
        db.commit()

        message = Message(
            conversation_id=conversation.id,
            content="Test",
            user_id="user1"
        )
        db.add(message)
        db.commit()
        db.refresh(message)

        assert message.conversation.id == conversation.id


@pytest.mark.unit
class TestDiagramModel:
    """Test cases for Diagram model"""

    def test_create_diagram(self, db):
        """Test creating a diagram"""
        # Create conversation
        conversation = Conversation(platform=PlatformType.WEB)
        db.add(conversation)
        db.commit()

        # Create diagram
        diagram = Diagram(
            conversation_id=conversation.id,
            plantuml_code="@startuml\n@enduml",
            drawio_xml="<mxfile></mxfile>",
            version=1,
            components_count=3,
            relationships_count=2
        )
        db.add(diagram)
        db.commit()
        db.refresh(diagram)

        assert diagram.id is not None
        assert diagram.version == 1
        assert diagram.components_count == 3
        assert diagram.created_at is not None

    def test_diagram_versioning(self, db):
        """Test diagram versioning"""
        conversation = Conversation(platform=PlatformType.WEB)
        db.add(conversation)
        db.commit()

        # Create version 1
        diagram_v1 = Diagram(
            conversation_id=conversation.id,
            plantuml_code="v1",
            version=1
        )
        db.add(diagram_v1)
        db.commit()

        # Create version 2
        diagram_v2 = Diagram(
            conversation_id=conversation.id,
            plantuml_code="v2",
            version=2
        )
        db.add(diagram_v2)
        db.commit()

        # Verify both versions exist
        diagrams = db.query(Diagram).filter(
            Diagram.conversation_id == conversation.id
        ).order_by(Diagram.version.desc()).all()

        assert len(diagrams) == 2
        assert diagrams[0].version == 2
        assert diagrams[1].version == 1


@pytest.mark.unit
class TestModificationModel:
    """Test cases for Modification model"""

    def test_create_modification(self, db):
        """Test creating a modification record"""
        # Create conversation and diagram
        conversation = Conversation(platform=PlatformType.WEB)
        db.add(conversation)
        db.commit()

        diagram = Diagram(
            conversation_id=conversation.id,
            plantuml_code="test",
            version=1
        )
        db.add(diagram)
        db.commit()

        # Create modification
        modification = Modification(
            diagram_id=diagram.id,
            request="Add Redis cache",
            success=True,
            user_id="user1"
        )
        db.add(modification)
        db.commit()
        db.refresh(modification)

        assert modification.id is not None
        assert modification.request == "Add Redis cache"
        assert modification.success is True
        assert modification.applied_at is not None

    def test_modification_diagram_relationship(self, db):
        """Test modification-diagram relationship"""
        conversation = Conversation(platform=PlatformType.WEB)
        db.add(conversation)
        db.commit()

        diagram = Diagram(
            conversation_id=conversation.id,
            plantuml_code="test",
            version=1
        )
        db.add(diagram)
        db.commit()

        modification = Modification(
            diagram_id=diagram.id,
            request="Test modification"
        )
        db.add(modification)
        db.commit()

        # Refresh diagram
        db.refresh(diagram)

        assert len(diagram.modifications) == 1
        assert diagram.modifications[0].request == "Test modification"
