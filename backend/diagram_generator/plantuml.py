from typing import List
from langchain_anthropic import ChatAnthropic
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from backend.config import settings
from backend.api.models.schemas import ArchitectureExtraction
import subprocess
import os
import logging

logger = logging.getLogger(__name__)


class PlantUMLGenerator:
    """Generates PlantUML diagrams from architecture extraction"""

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
        """Create prompt for generating PlantUML diagrams"""
        return ChatPromptTemplate.from_messages([
            ("system", """You are an expert at creating PlantUML component diagrams from architectural descriptions.

Generate a clear, well-structured PlantUML component diagram based on the provided architectural information.

Guidelines:
1. Use appropriate PlantUML syntax for component diagrams
2. Use proper component types:
   - component for services and applications
   - database for databases
   - queue for message queues
   - cloud for external services
   - interface for APIs
3. Use packages/rectangles to group related components
4. Add clear labels to relationships
5. Use stereotypes to indicate technology (e.g., <<PostgreSQL>>, <<Redis>>)
6. Arrange components logically (left to right data flow)
7. Keep it clean and readable

Important:
- ONLY output valid PlantUML code
- Start with @startuml and end with @enduml
- Use proper arrow syntax for relationships (-->, ->, ..)
- Add notes for additional context if needed

Example structure:
@startuml
!define RECTANGLE rectangle
skinparam componentStyle rectangle

component "API Gateway" as api <<Nginx>>
database "PostgreSQL" as db <<Database>>
component "Auth Service" as auth <<Python>>

api --> auth : authenticate
auth --> db : query users

@enduml

Now generate the diagram:"""),
            ("user", """Architecture Context:
{context}

Components:
{components}

Relationships:
{relationships}

Generate the PlantUML diagram:""")
        ])

    async def generate(
        self,
        architecture: ArchitectureExtraction
    ) -> str:
        """
        Generate PlantUML code from architecture extraction

        Args:
            architecture: ArchitectureExtraction with components and relationships

        Returns:
            PlantUML code as string
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
            plantuml_code = response.content.strip()

            # Clean up code blocks if present
            if plantuml_code.startswith("```"):
                lines = plantuml_code.split("\n")
                plantuml_code = "\n".join(lines[1:-1])

            # Ensure proper start and end tags
            if not plantuml_code.startswith("@startuml"):
                plantuml_code = "@startuml\n" + plantuml_code
            if not plantuml_code.strip().endswith("@enduml"):
                plantuml_code = plantuml_code + "\n@enduml"

            return plantuml_code

        except Exception as e:
            logger.error(f"Error generating PlantUML: {e}")
            # Return a basic fallback diagram
            return self._generate_fallback_diagram(architecture)

    def _generate_fallback_diagram(
        self,
        architecture: ArchitectureExtraction
    ) -> str:
        """Generate a basic PlantUML diagram as fallback"""
        lines = ["@startuml", "skinparam componentStyle rectangle", ""]

        # Add components
        for comp in architecture.components:
            comp_type = "component"
            if comp.type == "database":
                comp_type = "database"
            elif comp.type == "queue":
                comp_type = "queue"

            tech_label = f" <<{comp.technologies[0]}>>" if comp.technologies else ""
            lines.append(f'{comp_type} "{comp.name}" as {comp.name.replace(" ", "_")}{tech_label}')

        lines.append("")

        # Add relationships
        for rel in architecture.relationships:
            source = rel.source.replace(" ", "_")
            target = rel.target.replace(" ", "_")
            label = f" : {rel.label}" if rel.label else ""
            lines.append(f"{source} --> {target}{label}")

        lines.append("@enduml")
        return "\n".join(lines)

    async def render_to_png(
        self,
        plantuml_code: str,
        output_path: str
    ) -> bool:
        """
        Render PlantUML code to PNG file

        Args:
            plantuml_code: PlantUML code string
            output_path: Path to save PNG file

        Returns:
            True if successful, False otherwise
        """
        try:
            # Create temp file for PlantUML code
            temp_file = output_path.replace(".png", ".puml")
            with open(temp_file, "w") as f:
                f.write(plantuml_code)

            # Check if PlantUML JAR exists
            if os.path.exists(settings.PLANTUML_JAR_PATH):
                # Use PlantUML JAR
                result = subprocess.run(
                    ["java", "-jar", settings.PLANTUML_JAR_PATH, "-tpng", temp_file],
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                success = result.returncode == 0
            else:
                # Try using plantuml command if available
                result = subprocess.run(
                    ["plantuml", "-tpng", temp_file],
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                success = result.returncode == 0

            # Clean up temp file
            if os.path.exists(temp_file):
                os.remove(temp_file)

            return success

        except Exception as e:
            logger.error(f"Error rendering PlantUML to PNG: {e}")
            return False

    def validate_plantuml(self, code: str) -> bool:
        """
        Validate PlantUML code syntax

        Args:
            code: PlantUML code to validate

        Returns:
            True if valid, False otherwise
        """
        # Basic validation
        if not code.strip():
            return False

        if "@startuml" not in code or "@enduml" not in code:
            return False

        return True
