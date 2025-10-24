from typing import List, Dict, Any
from langchain_anthropic import ChatAnthropic
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from backend.config import settings
from backend.api.models.schemas import ArchitectureExtraction
import xml.etree.ElementTree as ET
import base64
import zlib
import logging

logger = logging.getLogger(__name__)


class DrawioGenerator:
    """Generates Draw.io XML diagrams from architecture extraction"""

    def __init__(self):
        self.llm = self._initialize_llm()
        self.generation_prompt = self._create_generation_prompt()

    def _initialize_llm(self):
        """Initialize the LLM based on configuration"""
        if settings.LLM_PROVIDER == "anthropic":
            return ChatAnthropic(
                model=settings.LLM_MODEL,
                anthropic_api_key=settings.ANTHROPIC_API_KEY,
                temperature=0.3
            )
        elif settings.LLM_PROVIDER == "openai":
            return ChatOpenAI(
                model=settings.LLM_MODEL,
                openai_api_key=settings.OPENAI_API_KEY,
                temperature=0.3
            )
        else:
            raise ValueError(f"Unsupported LLM provider: {settings.LLM_PROVIDER}")

    def _create_generation_prompt(self) -> ChatPromptTemplate:
        """Create prompt for generating Draw.io diagrams"""
        return ChatPromptTemplate.from_messages([
            ("system", """You are an expert at creating Draw.io (mxGraph) XML diagrams from architectural descriptions.

Generate a well-structured Draw.io XML diagram based on the provided architectural information.

Guidelines:
1. Use proper mxGraph XML structure
2. Position components logically (grid-based layout)
3. Use appropriate shapes for different component types:
   - Rectangles for services/components
   - Cylinder shapes for databases
   - Cloud shapes for external services
4. Add connectors with proper styling
5. Use colors to differentiate component types
6. Add labels to all components and relationships

Important:
- ONLY output valid Draw.io XML
- Include proper mxfile, diagram, and mxGraphModel structure
- Use integer coordinates for positioning
- Ensure all IDs are unique

Example structure:
<mxfile host="app.diagrams.net" modified="2024-01-01T00:00:00.000Z" agent="AI" version="22.0.0">
  <diagram name="Architecture" id="diagram1">
    <mxGraphModel dx="1422" dy="794" grid="1" gridSize="10" guides="1">
      <root>
        <mxCell id="0"/>
        <mxCell id="1" parent="0"/>
        <mxCell id="2" value="API Gateway" style="rounded=1;whiteSpace=wrap;html=1;" vertex="1" parent="1">
          <mxGeometry x="100" y="100" width="120" height="60" as="geometry"/>
        </mxCell>
      </root>
    </mxGraphModel>
  </diagram>
</mxfile>

Now generate the diagram:"""),
            ("user", """Architecture Context:
{context}

Components:
{components}

Relationships:
{relationships}

Generate the Draw.io XML diagram:""")
        ])

    async def generate(
        self,
        architecture: ArchitectureExtraction
    ) -> str:
        """
        Generate Draw.io XML from architecture extraction

        Args:
            architecture: ArchitectureExtraction with components and relationships

        Returns:
            Draw.io XML as string
        """
        try:
            # Format components
            components_str = "\n".join([
                f"- {comp.name} ({comp.type}): {', '.join(comp.technologies) if comp.technologies else 'N/A'}"
                for comp in architecture.components
            ])

            # Format relationships
            relationships_str = "\n".join([
                f"- {rel.source} -> {rel.target} ({rel.relationship_type}): {rel.label or 'N/A'}"
                for rel in architecture.relationships
            ])

            prompt = self.generation_prompt.format_messages(
                context=architecture.context,
                components=components_str,
                relationships=relationships_str
            )

            response = await self.llm.ainvoke(prompt)
            drawio_xml = response.content.strip()

            # Clean up code blocks if present
            if drawio_xml.startswith("```"):
                lines = drawio_xml.split("\n")
                drawio_xml = "\n".join(lines[1:-1])

            # Validate XML
            if not self.validate_drawio_xml(drawio_xml):
                logger.warning("Generated invalid Draw.io XML, using fallback")
                return self._generate_fallback_diagram(architecture)

            return drawio_xml

        except Exception as e:
            logger.error(f"Error generating Draw.io XML: {e}")
            return self._generate_fallback_diagram(architecture)

    def _generate_fallback_diagram(
        self,
        architecture: ArchitectureExtraction
    ) -> str:
        """Generate a basic Draw.io XML diagram as fallback"""
        # Component positioning
        x_offset = 100
        y_offset = 100
        width = 120
        height = 60
        spacing = 200

        components = architecture.components
        relationships = architecture.relationships

        # Create XML structure
        root = ET.Element("mxfile", {
            "host": "app.diagrams.net",
            "modified": "2024-01-01T00:00:00.000Z",
            "agent": "AI",
            "version": "22.0.0"
        })

        diagram = ET.SubElement(root, "diagram", {
            "name": "Architecture",
            "id": "diagram1"
        })

        graph_model = ET.SubElement(diagram, "mxGraphModel", {
            "dx": "1422",
            "dy": "794",
            "grid": "1",
            "gridSize": "10",
            "guides": "1"
        })

        graph_root = ET.SubElement(graph_model, "root")
        ET.SubElement(graph_root, "mxCell", {"id": "0"})
        ET.SubElement(graph_root, "mxCell", {"id": "1", "parent": "0"})

        # Add components
        component_map = {}
        for idx, comp in enumerate(components):
            cell_id = f"comp_{idx + 2}"
            component_map[comp.name] = cell_id

            # Determine style based on component type
            if comp.type == "database":
                style = "shape=cylinder3;whiteSpace=wrap;html=1;boundedLbl=1;backgroundOutline=1;size=15;fillColor=#dae8fc;strokeColor=#6c8ebf;"
            elif comp.type == "queue":
                style = "shape=hexagon;perimeter=hexagonPerimeter2;whiteSpace=wrap;html=1;fixedSize=1;fillColor=#fff2cc;strokeColor=#d6b656;"
            else:
                style = "rounded=1;whiteSpace=wrap;html=1;fillColor=#d5e8d4;strokeColor=#82b366;"

            cell = ET.SubElement(graph_root, "mxCell", {
                "id": cell_id,
                "value": comp.name,
                "style": style,
                "vertex": "1",
                "parent": "1"
            })

            # Position components in a grid
            row = idx // 3
            col = idx % 3
            x = x_offset + (col * spacing)
            y = y_offset + (row * spacing)

            ET.SubElement(cell, "mxGeometry", {
                "x": str(x),
                "y": str(y),
                "width": str(width),
                "height": str(height),
                "as": "geometry"
            })

        # Add relationships
        edge_id = len(components) + 2
        for rel in relationships:
            if rel.source in component_map and rel.target in component_map:
                cell = ET.SubElement(graph_root, "mxCell", {
                    "id": f"edge_{edge_id}",
                    "value": rel.label or rel.relationship_type,
                    "style": "edgeStyle=orthogonalEdgeStyle;rounded=0;orthogonalLoop=1;jettySize=auto;html=1;",
                    "edge": "1",
                    "parent": "1",
                    "source": component_map[rel.source],
                    "target": component_map[rel.target]
                })

                ET.SubElement(cell, "mxGeometry", {
                    "relative": "1",
                    "as": "geometry"
                })

                edge_id += 1

        # Convert to string
        return ET.tostring(root, encoding="unicode", method="xml")

    def validate_drawio_xml(self, xml_str: str) -> bool:
        """
        Validate Draw.io XML syntax

        Args:
            xml_str: Draw.io XML string

        Returns:
            True if valid, False otherwise
        """
        try:
            ET.fromstring(xml_str)
            return True
        except ET.ParseError:
            return False

    def format_xml(self, xml_str: str) -> str:
        """
        Format Draw.io XML for better readability

        Args:
            xml_str: Draw.io XML string

        Returns:
            Formatted XML string
        """
        try:
            root = ET.fromstring(xml_str)
            ET.indent(root, space="  ")
            return ET.tostring(root, encoding="unicode", method="xml")
        except Exception as e:
            logger.error(f"Error formatting XML: {e}")
            return xml_str
