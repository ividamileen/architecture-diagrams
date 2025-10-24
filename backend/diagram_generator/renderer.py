import subprocess
import os
import tempfile
from pathlib import Path
from PIL import Image
import logging

logger = logging.getLogger(__name__)


class DiagramRenderer:
    """Renders diagrams to PNG format"""

    @staticmethod
    async def render_plantuml_to_png(
        plantuml_code: str,
        output_path: str
    ) -> bool:
        """
        Render PlantUML code to PNG

        Args:
            plantuml_code: PlantUML code string
            output_path: Path to save PNG file

        Returns:
            True if successful, False otherwise
        """
        try:
            # Ensure output directory exists
            os.makedirs(os.path.dirname(output_path), exist_ok=True)

            # Create temp file for PlantUML code
            with tempfile.NamedTemporaryFile(mode='w', suffix='.puml', delete=False) as temp_file:
                temp_file.write(plantuml_code)
                temp_path = temp_file.name

            try:
                # Try using plantuml command
                result = subprocess.run(
                    ["plantuml", "-tpng", "-o", os.path.dirname(output_path), temp_path],
                    capture_output=True,
                    text=True,
                    timeout=30
                )

                if result.returncode == 0:
                    # PlantUML creates output with same name but .png extension
                    temp_png = temp_path.replace('.puml', '.png')
                    if os.path.exists(temp_png):
                        os.rename(temp_png, output_path)
                        return True

            except FileNotFoundError:
                logger.warning("plantuml command not found")

            return False

        except Exception as e:
            logger.error(f"Error rendering PlantUML to PNG: {e}")
            return False
        finally:
            # Clean up temp file
            if os.path.exists(temp_path):
                os.remove(temp_path)

    @staticmethod
    async def render_drawio_to_png(
        drawio_xml: str,
        output_path: str
    ) -> bool:
        """
        Render Draw.io XML to PNG
        Note: This requires draw.io CLI or headless browser
        For MVP, we'll create a placeholder implementation

        Args:
            drawio_xml: Draw.io XML string
            output_path: Path to save PNG file

        Returns:
            True if successful, False otherwise
        """
        try:
            # Ensure output directory exists
            os.makedirs(os.path.dirname(output_path), exist_ok=True)

            # Create temp file for Draw.io XML
            with tempfile.NamedTemporaryFile(mode='w', suffix='.drawio', delete=False) as temp_file:
                temp_file.write(drawio_xml)
                temp_path = temp_file.name

            try:
                # Try using draw.io desktop CLI if available
                result = subprocess.run(
                    ["drawio", "--export", "--format", "png", "--output", output_path, temp_path],
                    capture_output=True,
                    text=True,
                    timeout=30
                )

                success = result.returncode == 0 and os.path.exists(output_path)

                if success:
                    return True

            except FileNotFoundError:
                logger.warning("draw.io CLI not found")

            # Fallback: Create a placeholder image
            logger.info("Creating placeholder image for Draw.io diagram")
            return DiagramRenderer._create_placeholder_image(output_path, "Draw.io Diagram")

        except Exception as e:
            logger.error(f"Error rendering Draw.io to PNG: {e}")
            return False
        finally:
            # Clean up temp file
            if os.path.exists(temp_path):
                os.remove(temp_path)

    @staticmethod
    def _create_placeholder_image(output_path: str, text: str) -> bool:
        """
        Create a placeholder PNG image with text

        Args:
            output_path: Path to save PNG file
            text: Text to display on image

        Returns:
            True if successful
        """
        try:
            from PIL import Image, ImageDraw, ImageFont

            # Create a simple image
            width, height = 800, 600
            image = Image.new('RGB', (width, height), color='white')
            draw = ImageDraw.Draw(image)

            # Draw text
            try:
                font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 40)
            except:
                font = ImageFont.load_default()

            # Center text
            bbox = draw.textbbox((0, 0), text, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
            position = ((width - text_width) // 2, (height - text_height) // 2)

            draw.text(position, text, fill='black', font=font)

            # Save image
            image.save(output_path)
            return True

        except Exception as e:
            logger.error(f"Error creating placeholder image: {e}")
            return False

    @staticmethod
    def optimize_png(image_path: str, max_width: int = 1920, max_height: int = 1080) -> bool:
        """
        Optimize PNG image size and dimensions

        Args:
            image_path: Path to PNG file
            max_width: Maximum width in pixels
            max_height: Maximum height in pixels

        Returns:
            True if successful
        """
        try:
            with Image.open(image_path) as img:
                # Resize if needed
                if img.width > max_width or img.height > max_height:
                    img.thumbnail((max_width, max_height), Image.Resampling.LANCZOS)

                # Save optimized
                img.save(image_path, optimize=True, quality=85)

            return True

        except Exception as e:
            logger.error(f"Error optimizing PNG: {e}")
            return False
