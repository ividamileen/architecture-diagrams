from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import List
from backend.api.models import get_db
from backend.api.models.schemas import (
    DiagramGenerate,
    DiagramResponse,
    ModificationRequest,
    ModificationResponse
)
from backend.api.services import ConversationService, DiagramService
from backend.config import settings
import os
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/diagrams", tags=["diagrams"])


@router.post("/generate", response_model=DiagramResponse)
async def generate_diagram(
    request: DiagramGenerate,
    db: Session = Depends(get_db)
):
    """
    Generate a diagram from conversation messages
    """
    try:
        conversation_service = ConversationService(db)
        diagram_service = DiagramService(db)

        # Check if diagram already exists
        if not request.force_regenerate:
            existing_diagram = await diagram_service.get_latest_diagram(
                request.conversation_id
            )
            if existing_diagram:
                return DiagramResponse.model_validate(existing_diagram)

        # Get conversation context
        context = await conversation_service.get_conversation_context(
            request.conversation_id
        )

        if not context:
            raise HTTPException(
                status_code=400,
                detail="No technical messages found in conversation"
            )

        # Generate diagram
        diagram = await diagram_service.generate_diagram(
            request.conversation_id,
            context
        )

        return diagram

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating diagram: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/{diagram_id}", response_model=DiagramResponse)
async def get_diagram(
    diagram_id: int,
    db: Session = Depends(get_db)
):
    """
    Get a diagram by ID
    """
    try:
        diagram_service = DiagramService(db)
        diagram = await diagram_service.get_diagram(diagram_id)

        if not diagram:
            raise HTTPException(status_code=404, detail="Diagram not found")

        return DiagramResponse.model_validate(diagram)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting diagram: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/conversation/{conversation_id}", response_model=List[DiagramResponse])
async def get_conversation_diagrams(
    conversation_id: int,
    db: Session = Depends(get_db)
):
    """
    Get all diagrams for a conversation
    """
    try:
        diagram_service = DiagramService(db)
        diagrams = await diagram_service.get_conversation_diagrams(conversation_id)

        return [DiagramResponse.model_validate(d) for d in diagrams]

    except Exception as e:
        logger.error(f"Error getting diagrams: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/modify", response_model=ModificationResponse)
async def modify_diagram(
    modification: ModificationRequest,
    db: Session = Depends(get_db)
):
    """
    Modify a diagram based on natural language request
    """
    try:
        diagram_service = DiagramService(db)
        result = await diagram_service.modify_diagram(modification)

        return result

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error modifying diagram: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.put("/{diagram_id}/code")
async def update_diagram_code(
    diagram_id: int,
    plantuml_code: str = None,
    drawio_xml: str = None,
    db: Session = Depends(get_db)
):
    """
    Update diagram code directly (from editor)
    """
    try:
        diagram_service = DiagramService(db)
        diagram = await diagram_service.update_diagram_code(
            diagram_id,
            plantuml_code=plantuml_code,
            drawio_xml=drawio_xml
        )

        return diagram

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error updating diagram code: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/{diagram_id}/png")
async def get_diagram_png(
    diagram_id: int,
    db: Session = Depends(get_db)
):
    """
    Get diagram PNG image
    """
    try:
        diagram_service = DiagramService(db)
        diagram = await diagram_service.get_diagram(diagram_id)

        if not diagram:
            raise HTTPException(status_code=404, detail="Diagram not found")

        if not diagram.png_url:
            raise HTTPException(status_code=404, detail="PNG not available")

        # Convert URL to file path
        png_path = os.path.join(
            settings.DIAGRAM_STORAGE_PATH,
            os.path.basename(diagram.png_url)
        )

        if not os.path.exists(png_path):
            raise HTTPException(status_code=404, detail="PNG file not found")

        return FileResponse(
            png_path,
            media_type="image/png",
            filename=f"diagram_{diagram_id}.png"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting PNG: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/{diagram_id}/plantuml")
async def get_diagram_plantuml(
    diagram_id: int,
    db: Session = Depends(get_db)
):
    """
    Get diagram PlantUML code
    """
    try:
        diagram_service = DiagramService(db)
        diagram = await diagram_service.get_diagram(diagram_id)

        if not diagram:
            raise HTTPException(status_code=404, detail="Diagram not found")

        return {
            "diagram_id": diagram_id,
            "code": diagram.plantuml_code
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting PlantUML: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/{diagram_id}/drawio")
async def get_diagram_drawio(
    diagram_id: int,
    db: Session = Depends(get_db)
):
    """
    Get diagram Draw.io XML
    """
    try:
        diagram_service = DiagramService(db)
        diagram = await diagram_service.get_diagram(diagram_id)

        if not diagram:
            raise HTTPException(status_code=404, detail="Diagram not found")

        return {
            "diagram_id": diagram_id,
            "xml": diagram.drawio_xml
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting Draw.io XML: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
