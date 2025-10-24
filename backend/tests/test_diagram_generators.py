import pytest
from unittest.mock import Mock, patch, AsyncMock
from backend.diagram_generator.plantuml import PlantUMLGenerator
from backend.diagram_generator.drawio import DrawioGenerator
from backend.api.models.schemas import ArchitectureExtraction, ArchitectureEntity, ArchitectureRelationship


@pytest.mark.unit
class TestPlantUMLGenerator:
    """Test cases for PlantUML diagram generation"""

    @pytest.fixture
    def generator(self):
        """Create PlantUMLGenerator instance"""
        with patch('backend.diagram_generator.plantuml.ChatAnthropic'):
            return PlantUMLGenerator()

    @pytest.mark.asyncio
    async def test_generate_plantuml(self, generator, sample_architecture_extraction):
        """Test PlantUML generation"""
        mock_content = '''@startuml
component "API Gateway" as api
database "PostgreSQL" as db
api --> db : query
@enduml'''

        mock_response = Mock()
        mock_response.content = mock_content

        with patch.object(generator.llm, 'ainvoke', return_value=mock_response):
            result = await generator.generate(sample_architecture_extraction)

            assert "@startuml" in result
            assert "@enduml" in result
            assert "API Gateway" in result or "component" in result

    @pytest.mark.asyncio
    async def test_generate_plantuml_with_code_blocks(self, generator, sample_architecture_extraction):
        """Test PlantUML generation with markdown code blocks"""
        mock_content = '''```plantuml
@startuml
component "API Gateway"
@enduml
```'''

        mock_response = Mock()
        mock_response.content = mock_content

        with patch.object(generator.llm, 'ainvoke', return_value=mock_response):
            result = await generator.generate(sample_architecture_extraction)

            # Should strip code blocks
            assert "```" not in result
            assert "@startuml" in result

    def test_validate_plantuml_valid(self, generator):
        """Test PlantUML validation with valid code"""
        valid_code = "@startuml\ncomponent A\n@enduml"
        assert generator.validate_plantuml(valid_code) is True

    def test_validate_plantuml_invalid(self, generator):
        """Test PlantUML validation with invalid code"""
        invalid_code = "component A"  # Missing @startuml and @enduml
        assert generator.validate_plantuml(invalid_code) is False

    def test_validate_plantuml_empty(self, generator):
        """Test PlantUML validation with empty code"""
        assert generator.validate_plantuml("") is False

    @pytest.mark.asyncio
    async def test_generate_fallback_diagram(self, generator, sample_architecture_extraction):
        """Test fallback diagram generation"""
        result = generator._generate_fallback_diagram(sample_architecture_extraction)

        assert "@startuml" in result
        assert "@enduml" in result
        # Should include components from architecture
        assert any(comp.name.replace(" ", "_") in result for comp in sample_architecture_extraction.components)


@pytest.mark.unit
class TestDrawioGenerator:
    """Test cases for Draw.io diagram generation"""

    @pytest.fixture
    def generator(self):
        """Create DrawioGenerator instance"""
        with patch('backend.diagram_generator.drawio.ChatAnthropic'):
            return DrawioGenerator()

    @pytest.mark.asyncio
    async def test_generate_drawio(self, generator, sample_architecture_extraction):
        """Test Draw.io XML generation"""
        mock_content = '''<mxfile>
  <diagram name="Architecture">
    <mxGraphModel>
      <root>
        <mxCell id="0"/>
        <mxCell id="1" parent="0"/>
      </root>
    </mxGraphModel>
  </diagram>
</mxfile>'''

        mock_response = Mock()
        mock_response.content = mock_content

        with patch.object(generator.llm, 'ainvoke', return_value=mock_response):
            result = await generator.generate(sample_architecture_extraction)

            assert "<mxfile" in result
            assert "<diagram" in result

    def test_validate_drawio_xml_valid(self, generator):
        """Test Draw.io XML validation with valid XML"""
        valid_xml = '<mxfile><diagram></diagram></mxfile>'
        assert generator.validate_drawio_xml(valid_xml) is True

    def test_validate_drawio_xml_invalid(self, generator):
        """Test Draw.io XML validation with invalid XML"""
        invalid_xml = '<mxfile><diagram>'  # Unclosed tags
        assert generator.validate_drawio_xml(invalid_xml) is False

    @pytest.mark.asyncio
    async def test_generate_fallback_diagram(self, generator, sample_architecture_extraction):
        """Test fallback Draw.io diagram generation"""
        result = generator._generate_fallback_diagram(sample_architecture_extraction)

        assert "<mxfile" in result
        assert "<mxGraphModel" in result
        # Should validate as proper XML
        assert generator.validate_drawio_xml(result) is True

    def test_format_xml(self, generator):
        """Test XML formatting"""
        unformatted_xml = '<mxfile><diagram><mxGraphModel></mxGraphModel></diagram></mxfile>'
        formatted = generator.format_xml(unformatted_xml)

        # Should be properly formatted
        assert formatted is not None
        assert "<mxfile" in formatted

    @pytest.mark.asyncio
    async def test_generate_with_invalid_response(self, generator, sample_architecture_extraction):
        """Test handling of invalid LLM response"""
        mock_response = Mock()
        mock_response.content = "Invalid XML content"

        with patch.object(generator.llm, 'ainvoke', return_value=mock_response):
            result = await generator.generate(sample_architecture_extraction)

            # Should fall back to valid XML
            assert generator.validate_drawio_xml(result) is True
