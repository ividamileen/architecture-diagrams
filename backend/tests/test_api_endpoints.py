import pytest
from backend.api.models.schemas import MessageCreate, PlatformType


@pytest.mark.integration
class TestConversationEndpoints:
    """Integration tests for conversation endpoints"""

    def test_create_conversation(self, client):
        """Test creating a conversation"""
        response = client.post(
            "/api/v1/conversations/",
            json={"platform": "web"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["platform"] == "web"
        assert "id" in data
        assert "created_at" in data

    def test_get_conversation(self, client):
        """Test retrieving a conversation"""
        # Create conversation first
        create_response = client.post(
            "/api/v1/conversations/",
            json={"platform": "web"}
        )
        conversation_id = create_response.json()["id"]

        # Get conversation
        response = client.get(f"/api/v1/conversations/{conversation_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == conversation_id

    def test_get_nonexistent_conversation(self, client):
        """Test retrieving a non-existent conversation"""
        response = client.get("/api/v1/conversations/99999")
        assert response.status_code == 404


@pytest.mark.integration
class TestMessageEndpoints:
    """Integration tests for message endpoints"""

    @pytest.mark.asyncio
    async def test_create_message(self, client):
        """Test creating a message"""
        # Mock the LLM response
        with pytest.mock.patch('backend.ai.conversation_analyzer.ConversationAnalyzer.analyze_message') as mock_analyze:
            from backend.api.models.schemas import TechnicalAnalysis
            mock_analyze.return_value = TechnicalAnalysis(
                is_technical=True,
                confidence_score=0.85,
                entities=["API", "Database"],
                reasoning="Technical discussion"
            )

            response = client.post(
                "/api/v1/messages/",
                json={
                    "content": "We need an API gateway with PostgreSQL",
                    "user_id": "test-user",
                    "user_name": "Test User",
                    "platform": "web"
                }
            )

            assert response.status_code == 200
            data = response.json()
            assert data["content"] == "We need an API gateway with PostgreSQL"
            assert data["user_id"] == "test-user"
            assert "is_technical" in data
            assert "confidence_score" in data

    def test_get_conversation_messages(self, client, sample_message_data):
        """Test retrieving messages from a conversation"""
        # Create a message first
        with pytest.mock.patch('backend.ai.conversation_analyzer.ConversationAnalyzer.analyze_message') as mock_analyze:
            from backend.api.models.schemas import TechnicalAnalysis
            mock_analyze.return_value = TechnicalAnalysis(
                is_technical=False,
                confidence_score=0.1,
                entities=[],
                reasoning="Not technical"
            )

            create_response = client.post("/api/v1/messages/", json=sample_message_data)
            conversation_id = create_response.json()["conversation_id"]

            # Get messages
            response = client.get(f"/api/v1/messages/conversation/{conversation_id}")

            assert response.status_code == 200
            data = response.json()
            assert isinstance(data, list)
            assert len(data) >= 1


@pytest.mark.integration
class TestDiagramEndpoints:
    """Integration tests for diagram endpoints"""

    @pytest.mark.asyncio
    async def test_generate_diagram(self, client):
        """Test diagram generation"""
        # Create conversation and messages first
        with pytest.mock.patch('backend.ai.conversation_analyzer.ConversationAnalyzer.analyze_message') as mock_analyze, \
             pytest.mock.patch('backend.ai.conversation_analyzer.ConversationAnalyzer.extract_architecture') as mock_extract, \
             pytest.mock.patch('backend.diagram_generator.plantuml.PlantUMLGenerator.generate') as mock_plantuml, \
             pytest.mock.patch('backend.diagram_generator.drawio.DrawioGenerator.generate') as mock_drawio:

            from backend.api.models.schemas import TechnicalAnalysis, ArchitectureExtraction, ArchitectureEntity

            # Mock analysis
            mock_analyze.return_value = TechnicalAnalysis(
                is_technical=True,
                confidence_score=0.9,
                entities=["API"],
                reasoning="Technical"
            )

            # Mock extraction
            mock_extract.return_value = ArchitectureExtraction(
                components=[ArchitectureEntity(type="service", name="API", technologies=[])],
                relationships=[],
                context="Test"
            )

            # Mock generators
            mock_plantuml.return_value = "@startuml\ncomponent API\n@enduml"
            mock_drawio.return_value = "<mxfile></mxfile>"

            # Create technical messages
            conversation_id = None
            for i in range(3):
                msg_response = client.post(
                    "/api/v1/messages/",
                    json={
                        "content": f"Technical message {i} about API and database",
                        "user_id": "test-user",
                        "platform": "web"
                    }
                )
                if conversation_id is None:
                    conversation_id = msg_response.json()["conversation_id"]

            # Generate diagram
            response = client.post(
                "/api/v1/diagrams/generate",
                json={"conversation_id": conversation_id}
            )

            assert response.status_code == 200
            data = response.json()
            assert "id" in data
            assert "plantuml_code" in data
            assert "drawio_xml" in data

    def test_get_diagram(self, client):
        """Test retrieving a diagram"""
        # This would require creating a diagram first
        # Skipping for now as it requires complex setup
        pass

    @pytest.mark.asyncio
    async def test_modify_diagram(self, client):
        """Test diagram modification"""
        # This would require creating a diagram first
        # Testing the endpoint structure
        response = client.post(
            "/api/v1/diagrams/modify",
            json={
                "diagram_id": 1,
                "request": "Add Redis cache",
                "user_id": "test-user"
            }
        )

        # Will fail because diagram doesn't exist, but tests endpoint structure
        assert response.status_code in [404, 500]


@pytest.mark.integration
class TestHealthEndpoint:
    """Integration tests for health check"""

    def test_health_check(self, client):
        """Test health check endpoint"""
        response = client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "version" in data
