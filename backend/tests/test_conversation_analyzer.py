import pytest
from unittest.mock import Mock, patch, AsyncMock
from backend.ai.conversation_analyzer import ConversationAnalyzer
from backend.api.models.schemas import TechnicalAnalysis


@pytest.mark.unit
class TestConversationAnalyzer:
    """Test cases for ConversationAnalyzer"""

    @pytest.fixture
    def analyzer(self):
        """Create ConversationAnalyzer instance"""
        with patch('backend.ai.conversation_analyzer.ChatAnthropic'):
            return ConversationAnalyzer()

    @pytest.mark.asyncio
    async def test_analyze_technical_message(self, analyzer, mock_llm_response):
        """Test analyzing a technical message"""
        # Mock LLM response
        mock_content = '{"is_technical": true, "confidence_score": 0.85, "entities": ["API", "Database"], "reasoning": "Technical discussion"}'
        mock_response = Mock()
        mock_response.content = mock_content

        with patch.object(analyzer.llm, 'ainvoke', return_value=mock_response):
            result = await analyzer.analyze_message(
                message="We need an API gateway with PostgreSQL",
                context=[]
            )

            assert isinstance(result, TechnicalAnalysis)
            assert result.is_technical is True
            assert result.confidence_score == 0.85
            assert "API" in result.entities or "Database" in result.entities

    @pytest.mark.asyncio
    async def test_analyze_non_technical_message(self, analyzer):
        """Test analyzing a non-technical message"""
        mock_content = '{"is_technical": false, "confidence_score": 0.1, "entities": [], "reasoning": "General conversation"}'
        mock_response = Mock()
        mock_response.content = mock_content

        with patch.object(analyzer.llm, 'ainvoke', return_value=mock_response):
            result = await analyzer.analyze_message(
                message="Hello, how are you?",
                context=[]
            )

            assert result.is_technical is False
            assert result.confidence_score < 0.5

    @pytest.mark.asyncio
    async def test_extract_architecture(self, analyzer, sample_technical_messages):
        """Test architecture extraction from messages"""
        mock_content = '''{
            "components": [
                {"type": "gateway", "name": "API Gateway", "technologies": ["Nginx"]},
                {"type": "database", "name": "PostgreSQL", "technologies": ["PostgreSQL"]}
            ],
            "relationships": [
                {"source": "API Gateway", "target": "PostgreSQL", "relationship_type": "data_flow", "label": "query"}
            ],
            "context": "API architecture"
        }'''
        mock_response = Mock()
        mock_response.content = mock_content

        with patch.object(analyzer.llm, 'ainvoke', return_value=mock_response):
            result = await analyzer.extract_architecture(sample_technical_messages)

            assert len(result.components) >= 1
            assert len(result.relationships) >= 0
            assert result.context != ""

    @pytest.mark.asyncio
    async def test_analyze_message_with_context(self, analyzer):
        """Test analyzing message with context"""
        context = [
            "We're building a microservices architecture",
            "Using Docker and Kubernetes"
        ]

        mock_content = '{"is_technical": true, "confidence_score": 0.9, "entities": ["microservices"], "reasoning": "Architectural discussion"}'
        mock_response = Mock()
        mock_response.content = mock_content

        with patch.object(analyzer.llm, 'ainvoke', return_value=mock_response):
            result = await analyzer.analyze_message(
                message="We need an API gateway",
                context=context
            )

            assert result.is_technical is True
            assert result.confidence_score >= 0.7

    @pytest.mark.asyncio
    async def test_should_trigger_diagram_generation_positive(self, analyzer):
        """Test diagram generation trigger with high confidence"""
        analysis = TechnicalAnalysis(
            is_technical=True,
            confidence_score=0.8,
            entities=["API", "Database"],
            reasoning="Technical discussion"
        )

        result = analyzer.should_trigger_diagram_generation(analysis)
        assert result is True

    @pytest.mark.asyncio
    async def test_should_trigger_diagram_generation_negative(self, analyzer):
        """Test diagram generation trigger with low confidence"""
        analysis = TechnicalAnalysis(
            is_technical=False,
            confidence_score=0.3,
            entities=[],
            reasoning="General conversation"
        )

        result = analyzer.should_trigger_diagram_generation(analysis)
        assert result is False

    @pytest.mark.asyncio
    async def test_analyze_message_error_handling(self, analyzer):
        """Test error handling in message analysis"""
        with patch.object(analyzer.llm, 'ainvoke', side_effect=Exception("API Error")):
            result = await analyzer.analyze_message(
                message="Test message",
                context=[]
            )

            # Should return safe defaults on error
            assert result.is_technical is False
            assert result.confidence_score == 0.0
            assert "Error during analysis" in result.reasoning
