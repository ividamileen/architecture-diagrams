from typing import Dict, Any
from langchain_anthropic import ChatAnthropic
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from backend.config import settings
import logging

logger = logging.getLogger(__name__)


class DiagramModifier:
    """Modifies diagrams based on natural language requests"""

    def __init__(self):
        self.llm = self._initialize_llm()
        self.plantuml_modification_prompt = self._create_plantuml_modification_prompt()
        self.drawio_modification_prompt = self._create_drawio_modification_prompt()

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

    def _create_plantuml_modification_prompt(self) -> ChatPromptTemplate:
        """Create prompt for modifying PlantUML diagrams"""
        return ChatPromptTemplate.from_messages([
            ("system", """You are an expert at PlantUML diagram generation and modification.

Your task is to modify existing PlantUML code based on user requests.

Common modifications:
- Adding new components (services, databases, APIs, etc.)
- Adding relationships between components
- Modifying labels and descriptions
- Reorganizing layout
- Changing component types or stereotypes
- Adding grouping/packages

Rules:
1. Preserve existing components unless explicitly asked to remove them
2. Maintain proper PlantUML syntax
3. Use appropriate component types and relationships
4. Keep the diagram clean and readable
5. Only output valid PlantUML code, no explanations

Current PlantUML code:
{current_code}

User request:
{modification_request}

Output the modified PlantUML code:"""),
            ("user", "{modification_request}")
        ])

    def _create_drawio_modification_prompt(self) -> ChatPromptTemplate:
        """Create prompt for modifying Draw.io XML diagrams"""
        return ChatPromptTemplate.from_messages([
            ("system", """You are an expert at Draw.io diagram XML generation and modification.

Your task is to modify existing Draw.io XML based on user requests.

Rules:
1. Preserve existing elements unless explicitly asked to remove them
2. Maintain valid mxGraph XML structure
3. Properly position new elements
4. Use appropriate styles and connectors
5. Only output valid Draw.io XML, no explanations

Current Draw.io XML:
{current_xml}

User request:
{modification_request}

Output the modified Draw.io XML:"""),
            ("user", "{modification_request}")
        ])

    async def modify_plantuml(
        self,
        current_code: str,
        modification_request: str
    ) -> Dict[str, Any]:
        """
        Modify PlantUML diagram based on natural language request

        Args:
            current_code: Current PlantUML code
            modification_request: User's modification request

        Returns:
            Dict with 'success', 'code', and optional 'error' keys
        """
        try:
            prompt = self.plantuml_modification_prompt.format_messages(
                current_code=current_code,
                modification_request=modification_request
            )

            response = await self.llm.ainvoke(prompt)
            modified_code = response.content.strip()

            # Remove markdown code blocks if present
            if modified_code.startswith("```"):
                lines = modified_code.split("\n")
                modified_code = "\n".join(lines[1:-1])

            return {
                "success": True,
                "code": modified_code,
                "error": None
            }

        except Exception as e:
            logger.error(f"Error modifying PlantUML: {e}")
            return {
                "success": False,
                "code": current_code,
                "error": str(e)
            }

    async def modify_drawio(
        self,
        current_xml: str,
        modification_request: str
    ) -> Dict[str, Any]:
        """
        Modify Draw.io XML based on natural language request

        Args:
            current_xml: Current Draw.io XML
            modification_request: User's modification request

        Returns:
            Dict with 'success', 'xml', and optional 'error' keys
        """
        try:
            prompt = self.drawio_modification_prompt.format_messages(
                current_xml=current_xml,
                modification_request=modification_request
            )

            response = await self.llm.ainvoke(prompt)
            modified_xml = response.content.strip()

            # Remove markdown code blocks if present
            if modified_xml.startswith("```"):
                lines = modified_xml.split("\n")
                modified_xml = "\n".join(lines[1:-1])

            return {
                "success": True,
                "xml": modified_xml,
                "error": None
            }

        except Exception as e:
            logger.error(f"Error modifying Draw.io XML: {e}")
            return {
                "success": False,
                "xml": current_xml,
                "error": str(e)
            }
