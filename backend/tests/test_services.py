import pytest
from unittest.mock import Mock, patch
from sqlalchemy.orm import Session
from backend.api.services.conversation_service import ConversationService
from backend.api.services.diagram_service import DiagramService
from backend.api.models.schemas import MessageCreate, PlatformType, TechnicalAnalysis


@pytest.mark.unit
class TestConversationService:
    """Test cases for ConversationService"""

    @pytest.mark.asyncio
    async def test_create_conversation(self, db):
        """Test creating a conversation"""
        from backend.api.models.schemas import ConversationCreate

        service = ConversationService(db)
        conversation = await service.create_conversation(
            ConversationCreate(platform=PlatformType.WEB)
        )

        assert conversation.id is not None
        assert conversation.platform == PlatformType.WEB

    @pytest.mark.asyncio
    async def test_get_conversation(self, db):
        """Test retrieving a conversation"""
        from backend.api.models.schemas import ConversationCreate

        service = ConversationService(db)
        created = await service.create_conversation(
            ConversationCreate(platform=PlatformType.WEB)
        )

        retrieved = await service.get_conversation(created.id)
        assert retrieved is not None
        assert retrieved.id == created.id

    @pytest.mark.asyncio
    async def test_get_nonexistent_conversation(self, db):
        """Test retrieving a non-existent conversation"""
        service = ConversationService(db)
        result = await service.get_conversation(99999)
        assert result is None

    @pytest.mark.asyncio
    async def test_add_message(self, db, sample_message_data):
        """Test adding a message"""
        with patch.object(ConversationService, 'get_recent_messages', return_value=[]), \
             patch('backend.ai.conversation_analyzer.ConversationAnalyzer.analyze_message') as mock_analyze:

            mock_analyze.return_value = TechnicalAnalysis(
                is_technical=True,
                confidence_score=0.85,
                entities=["API", "Database"],
                reasoning="Technical discussion"
            )

            service = ConversationService(db)
            message_create = MessageCreate(**sample_message_data)

            message = await service.add_message(message_create)

            assert message.id is not None
            assert message.content == sample_message_data["content"]
            assert message.is_technical is True
            assert message.confidence_score == 0.85

    @pytest.mark.asyncio
    async def test_get_technical_messages(self, db):
        """Test retrieving technical messages"""
        with patch.object(ConversationService, 'get_recent_messages', return_value=[]), \
             patch('backend.ai.conversation_analyzer.ConversationAnalyzer.analyze_message') as mock_analyze:

            # Create conversation and messages
            from backend.api.models.schemas import ConversationCreate
            service = ConversationService(db)
            conversation = await service.create_conversation(
                ConversationCreate(platform=PlatformType.WEB)
            )

            # Add technical message
            mock_analyze.return_value = TechnicalAnalysis(
                is_technical=True,
                confidence_score=0.9,
                entities=["API"],
                reasoning="Technical"
            )

            await service.add_message(MessageCreate(
                content="Technical message about API",
                user_id="user1",
                conversation_id=conversation.id,
                platform=PlatformType.WEB
            ))

            # Add non-technical message
            mock_analyze.return_value = TechnicalAnalysis(
                is_technical=False,
                confidence_score=0.1,
                entities=[],
                reasoning="Not technical"
            )

            await service.add_message(MessageCreate(
                content="Hello everyone",
                user_id="user1",
                conversation_id=conversation.id,
                platform=PlatformType.WEB
            ))

            # Retrieve technical messages
            technical = await service.get_technical_messages(conversation.id)

            assert len(technical) == 1
            assert technical[0].is_technical is True

    @pytest.mark.asyncio
    async def test_should_generate_diagram(self, db):
        """Test diagram generation decision"""
        with patch.object(ConversationService, 'get_technical_messages') as mock_get:
            from backend.api.models import Message

            # Create mock technical messages
            mock_messages = [
                Mock(spec=Message, confidence_score=0.8),
                Mock(spec=Message, confidence_score=0.85),
                Mock(spec=Message, confidence_score=0.9)
            ]
            mock_get.return_value = mock_messages

            service = ConversationService(db)
            result = await service.should_generate_diagram(1)

            assert result is True


@pytest.mark.unit
class TestDiagramService:
    """Test cases for DiagramService"""

    @pytest.mark.asyncio
    async def test_generate_diagram(self, db, sample_technical_messages, sample_architecture_extraction):
        """Test diagram generation"""
        with patch('backend.ai.conversation_analyzer.ConversationAnalyzer.extract_architecture') as mock_extract, \
             patch('backend.diagram_generator.plantuml.PlantUMLGenerator.generate') as mock_plantuml, \
             patch('backend.diagram_generator.drawio.DrawioGenerator.generate') as mock_drawio, \
             patch.object(DiagramService, '_render_diagram_to_png', return_value="/diagrams/test.png"):

            mock_extract.return_value = sample_architecture_extraction
            mock_plantuml.return_value = "@startuml\ncomponent API\n@enduml"
            mock_drawio.return_value = "<mxfile></mxfile>"

            service = DiagramService(db)
            diagram = await service.generate_diagram(1, sample_technical_messages)

            assert diagram.id is not None
            assert diagram.plantuml_code is not None
            assert diagram.drawio_xml is not None
            assert diagram.components_count > 0

    @pytest.mark.asyncio
    async def test_get_diagram(self, db):
        """Test retrieving a diagram"""
        service = DiagramService(db)
        result = await service.get_diagram(1)

        # Will be None as no diagram exists
        assert result is None

    @pytest.mark.asyncio
    async def test_modify_diagram(self, db):
        """Test diagram modification"""
        # This would require creating a diagram first
        # Testing the service structure
        service = DiagramService(db)

        # Should raise error for non-existent diagram
        from backend.api.models.schemas import ModificationRequest
        with pytest.raises(ValueError):
            await service.modify_diagram(
                ModificationRequest(
                    diagram_id=99999,
                    request="Add Redis",
                    user_id="test-user"
                )
            )
