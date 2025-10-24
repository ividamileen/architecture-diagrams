from typing import Optional, List
from sqlalchemy.orm import Session
from backend.api.models import Diagram, Modification, Conversation
from backend.api.models.schemas import DiagramResponse, ModificationRequest, ModificationResponse
from backend.ai import ConversationAnalyzer, DiagramModifier
from backend.diagram_generator import PlantUMLGenerator, DrawioGenerator, DiagramRenderer
from backend.config import settings
import os
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class DiagramService:
    """Service for generating and managing diagrams"""

    def __init__(self, db: Session):
        self.db = db
        self.analyzer = ConversationAnalyzer()
        self.plantuml_generator = PlantUMLGenerator()
        self.drawio_generator = DrawioGenerator()
        self.modifier = DiagramModifier()
        self.renderer = DiagramRenderer()

    async def generate_diagram(
        self,
        conversation_id: int,
        messages: List[dict]
    ) -> DiagramResponse:
        """
        Generate diagram from conversation messages

        Args:
            conversation_id: ID of the conversation
            messages: List of message dicts with content and user_name

        Returns:
            DiagramResponse with generated diagram
        """
        try:
            # Extract architecture from messages
            architecture = await self.analyzer.extract_architecture(messages)

            # Generate PlantUML
            plantuml_code = await self.plantuml_generator.generate(architecture)

            # Generate Draw.io XML
            drawio_xml = await self.drawio_generator.generate(architecture)

            # Create diagram record
            diagram = Diagram(
                conversation_id=conversation_id,
                plantuml_code=plantuml_code,
                drawio_xml=drawio_xml,
                version=1,
                components_count=len(architecture.components),
                relationships_count=len(architecture.relationships)
            )

            self.db.add(diagram)
            self.db.commit()
            self.db.refresh(diagram)

            # Render to PNG (asynchronously in background)
            png_path = await self._render_diagram_to_png(diagram.id, plantuml_code)
            if png_path:
                diagram.png_url = png_path
                self.db.commit()
                self.db.refresh(diagram)

            logger.info(f"Generated diagram {diagram.id} for conversation {conversation_id}")

            return DiagramResponse.model_validate(diagram)

        except Exception as e:
            logger.error(f"Error generating diagram: {e}")
            raise

    async def get_diagram(self, diagram_id: int) -> Optional[Diagram]:
        """Get diagram by ID"""
        return self.db.query(Diagram).filter(Diagram.id == diagram_id).first()

    async def get_latest_diagram(self, conversation_id: int) -> Optional[Diagram]:
        """Get latest diagram for a conversation"""
        return self.db.query(Diagram).filter(
            Diagram.conversation_id == conversation_id
        ).order_by(Diagram.version.desc()).first()

    async def get_conversation_diagrams(
        self,
        conversation_id: int
    ) -> List[Diagram]:
        """Get all diagrams for a conversation"""
        return self.db.query(Diagram).filter(
            Diagram.conversation_id == conversation_id
        ).order_by(Diagram.version.desc()).all()

    async def modify_diagram(
        self,
        modification: ModificationRequest
    ) -> ModificationResponse:
        """
        Modify a diagram based on natural language request

        Args:
            modification: ModificationRequest with diagram_id and request

        Returns:
            ModificationResponse with new diagram
        """
        try:
            # Get original diagram
            original_diagram = await self.get_diagram(modification.diagram_id)
            if not original_diagram:
                raise ValueError(f"Diagram {modification.diagram_id} not found")

            # Modify PlantUML
            plantuml_result = await self.modifier.modify_plantuml(
                original_diagram.plantuml_code,
                modification.request
            )

            # Modify Draw.io XML
            drawio_result = await self.modifier.modify_drawio(
                original_diagram.drawio_xml,
                modification.request
            )

            if not plantuml_result["success"] and not drawio_result["success"]:
                # Both modifications failed
                mod_record = Modification(
                    diagram_id=modification.diagram_id,
                    request=modification.request,
                    success=False,
                    error_message="Failed to modify diagram",
                    user_id=modification.user_id
                )
                self.db.add(mod_record)
                self.db.commit()

                return ModificationResponse(
                    id=mod_record.id,
                    diagram_id=modification.diagram_id,
                    request=modification.request,
                    applied_at=mod_record.applied_at,
                    success=False,
                    error_message="Failed to modify diagram",
                    new_diagram=None
                )

            # Create new diagram version
            new_version = original_diagram.version + 1
            new_diagram = Diagram(
                conversation_id=original_diagram.conversation_id,
                plantuml_code=plantuml_result["code"],
                drawio_xml=drawio_result["xml"],
                version=new_version,
                components_count=original_diagram.components_count,  # Could recalculate
                relationships_count=original_diagram.relationships_count
            )

            self.db.add(new_diagram)
            self.db.commit()
            self.db.refresh(new_diagram)

            # Render new diagram to PNG
            png_path = await self._render_diagram_to_png(
                new_diagram.id,
                new_diagram.plantuml_code
            )
            if png_path:
                new_diagram.png_url = png_path
                self.db.commit()
                self.db.refresh(new_diagram)

            # Record modification
            mod_record = Modification(
                diagram_id=new_diagram.id,
                request=modification.request,
                success=True,
                user_id=modification.user_id
            )
            self.db.add(mod_record)
            self.db.commit()

            logger.info(f"Modified diagram {modification.diagram_id} -> {new_diagram.id}")

            return ModificationResponse(
                id=mod_record.id,
                diagram_id=new_diagram.id,
                request=modification.request,
                applied_at=mod_record.applied_at,
                success=True,
                error_message=None,
                new_diagram=DiagramResponse.model_validate(new_diagram)
            )

        except Exception as e:
            logger.error(f"Error modifying diagram: {e}")
            raise

    async def _render_diagram_to_png(
        self,
        diagram_id: int,
        plantuml_code: str
    ) -> Optional[str]:
        """
        Render diagram to PNG and return URL

        Args:
            diagram_id: ID of the diagram
            plantuml_code: PlantUML code to render

        Returns:
            URL/path to PNG file or None if failed
        """
        try:
            # Ensure diagram storage directory exists
            os.makedirs(settings.DIAGRAM_STORAGE_PATH, exist_ok=True)

            # Generate filename
            filename = f"diagram_{diagram_id}_{int(datetime.utcnow().timestamp())}.png"
            output_path = os.path.join(settings.DIAGRAM_STORAGE_PATH, filename)

            # Render to PNG
            success = await self.renderer.render_plantuml_to_png(
                plantuml_code,
                output_path
            )

            if success and os.path.exists(output_path):
                # Optimize PNG
                self.renderer.optimize_png(output_path)
                return f"/diagrams/{filename}"

            return None

        except Exception as e:
            logger.error(f"Error rendering diagram to PNG: {e}")
            return None

    async def update_diagram_code(
        self,
        diagram_id: int,
        plantuml_code: Optional[str] = None,
        drawio_xml: Optional[str] = None
    ) -> DiagramResponse:
        """
        Update diagram code directly (from editor)

        Args:
            diagram_id: ID of the diagram
            plantuml_code: New PlantUML code
            drawio_xml: New Draw.io XML

        Returns:
            Updated DiagramResponse
        """
        diagram = await self.get_diagram(diagram_id)
        if not diagram:
            raise ValueError(f"Diagram {diagram_id} not found")

        # Update code
        if plantuml_code is not None:
            diagram.plantuml_code = plantuml_code

            # Re-render PNG
            png_path = await self._render_diagram_to_png(diagram_id, plantuml_code)
            if png_path:
                diagram.png_url = png_path

        if drawio_xml is not None:
            diagram.drawio_xml = drawio_xml

        self.db.commit()
        self.db.refresh(diagram)

        return DiagramResponse.model_validate(diagram)
