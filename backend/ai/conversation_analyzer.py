from typing import List, Dict, Any
from langchain_anthropic import ChatAnthropic
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain.output_parsers import PydanticOutputParser
from backend.config import settings
from backend.api.models.schemas import TechnicalAnalysis, ArchitectureExtraction, ArchitectureEntity, ArchitectureRelationship
import json
import logging

logger = logging.getLogger(__name__)


class ConversationAnalyzer:
    """Analyzes conversations to detect technical/architectural discussions"""

    def __init__(self):
        self.llm = self._initialize_llm()
        self.technical_detection_prompt = self._create_technical_detection_prompt()
        self.architecture_extraction_prompt = self._create_architecture_extraction_prompt()

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

    def _create_technical_detection_prompt(self) -> ChatPromptTemplate:
        """Create prompt for detecting technical conversations"""
        return ChatPromptTemplate.from_messages([
            ("system", """You are an expert at analyzing conversations to detect technical and architectural discussions.

Your task is to analyze messages and determine if they are discussing system architecture, software design, or technical infrastructure.

Look for:
- Architecture keywords: microservices, monolith, architecture, design patterns, system design
- Infrastructure: servers, cloud, AWS, Azure, GCP, Kubernetes, Docker
- Components: services, APIs, databases, caches, queues, load balancers
- Technologies: PostgreSQL, Redis, MongoDB, Kafka, RabbitMQ, Nginx
- Technical concepts: scalability, performance, security, deployment
- Data flows and relationships between components
- Technical decisions and trade-offs

Ignore:
- General greetings and chitchat
- Non-technical discussions
- Project management without technical details
- Business requirements without architecture context

Respond with a JSON object containing:
{{
    "is_technical": true/false,
    "confidence_score": 0.0-1.0,
    "entities": ["entity1", "entity2", ...],
    "reasoning": "Brief explanation of your decision"
}}
"""),
            ("user", """Analyze this message:

Message: {message}

Previous context (last few messages):
{context}

Provide your analysis:""")
        ])

    def _create_architecture_extraction_prompt(self) -> ChatPromptTemplate:
        """Create prompt for extracting architecture from conversations"""
        return ChatPromptTemplate.from_messages([
            ("system", """You are an expert system architect who extracts architectural information from technical conversations.

Analyze the conversation and identify:
1. **Components**: Services, databases, APIs, caches, queues, frontends, backends, etc.
2. **Relationships**: How components interact (API calls, data flows, dependencies)
3. **Technologies**: Specific technologies mentioned (PostgreSQL, Redis, React, etc.)

Be precise and only extract information explicitly mentioned or clearly implied in the conversation.

Respond with a JSON object:
{{
    "components": [
        {{
            "type": "service|database|api|queue|cache|frontend|backend|loadbalancer|gateway",
            "name": "Component Name",
            "technologies": ["tech1", "tech2"]
        }}
    ],
    "relationships": [
        {{
            "source": "Component A",
            "target": "Component B",
            "relationship_type": "api_call|data_flow|dependency|authentication|storage",
            "label": "optional description"
        }}
    ],
    "context": "Brief summary of the architecture being discussed"
}}
"""),
            ("user", """Extract architecture information from this conversation:

{conversation}

Provide the architectural extraction:""")
        ])

    async def analyze_message(
        self,
        message: str,
        context: List[str] = None
    ) -> TechnicalAnalysis:
        """
        Analyze a single message to determine if it's technical

        Args:
            message: The message to analyze
            context: Previous messages for context

        Returns:
            TechnicalAnalysis with is_technical, confidence_score, entities, and reasoning
        """
        try:
            context_str = "\n".join(context[-5:]) if context else "No previous context"

            prompt = self.technical_detection_prompt.format_messages(
                message=message,
                context=context_str
            )

            response = await self.llm.ainvoke(prompt)
            result = json.loads(response.content)

            return TechnicalAnalysis(
                is_technical=result.get("is_technical", False),
                confidence_score=result.get("confidence_score", 0.0),
                entities=result.get("entities", []),
                reasoning=result.get("reasoning", "")
            )

        except Exception as e:
            logger.error(f"Error analyzing message: {e}")
            return TechnicalAnalysis(
                is_technical=False,
                confidence_score=0.0,
                entities=[],
                reasoning=f"Error during analysis: {str(e)}"
            )

    async def extract_architecture(
        self,
        messages: List[Dict[str, str]]
    ) -> ArchitectureExtraction:
        """
        Extract architectural components and relationships from a conversation

        Args:
            messages: List of message dicts with 'content' and 'user_name' keys

        Returns:
            ArchitectureExtraction with components, relationships, and context
        """
        try:
            # Format conversation
            conversation = "\n".join([
                f"{msg.get('user_name', 'User')}: {msg['content']}"
                for msg in messages
            ])

            prompt = self.architecture_extraction_prompt.format_messages(
                conversation=conversation
            )

            response = await self.llm.ainvoke(prompt)
            result = json.loads(response.content)

            # Parse components
            components = [
                ArchitectureEntity(
                    type=comp["type"],
                    name=comp["name"],
                    technologies=comp.get("technologies", [])
                )
                for comp in result.get("components", [])
            ]

            # Parse relationships
            relationships = [
                ArchitectureRelationship(
                    source=rel["source"],
                    target=rel["target"],
                    relationship_type=rel["relationship_type"],
                    label=rel.get("label")
                )
                for rel in result.get("relationships", [])
            ]

            return ArchitectureExtraction(
                components=components,
                relationships=relationships,
                context=result.get("context", "")
            )

        except Exception as e:
            logger.error(f"Error extracting architecture: {e}")
            return ArchitectureExtraction(
                components=[],
                relationships=[],
                context=f"Error during extraction: {str(e)}"
            )

    def should_trigger_diagram_generation(
        self,
        analysis: TechnicalAnalysis
    ) -> bool:
        """
        Determine if a diagram should be generated based on analysis

        Args:
            analysis: TechnicalAnalysis result

        Returns:
            True if diagram generation should be triggered
        """
        return (
            analysis.is_technical and
            analysis.confidence_score >= settings.TECHNICAL_CONFIDENCE_THRESHOLD
        )
