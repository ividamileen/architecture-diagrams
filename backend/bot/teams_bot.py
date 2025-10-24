from botbuilder.core import ActivityHandler, TurnContext, MessageFactory
from botbuilder.schema import ChannelAccount, Activity, ActivityTypes
from botbuilder.schema.teams import TeamsChannelAccount
from backend.api.services import ConversationService, DiagramService
from backend.api.models import get_db
from backend.api.models.schemas import MessageCreate, PlatformType
from backend.config import settings
import json
import logging

logger = logging.getLogger(__name__)


class ArchitectureDiagramBot(ActivityHandler):
    """
    Microsoft Teams bot for architecture diagram generation
    """

    def __init__(self):
        super().__init__()
        self.db_session = None

    async def on_message_activity(self, turn_context: TurnContext):
        """
        Handle incoming messages from Teams
        """
        try:
            # Get message details
            text = turn_context.activity.text.strip()
            user_id = turn_context.activity.from_property.id
            user_name = turn_context.activity.from_property.name
            conversation_id = turn_context.activity.conversation.id
            channel_id = self._get_channel_id(turn_context)

            logger.info(f"Received message from {user_name}: {text}")

            # Handle bot commands
            if text.startswith("@DiagramBot") or turn_context.activity.text.startswith("<at>"):
                await self._handle_bot_command(turn_context, text, user_id, user_name)
                return

            # Process regular message
            db = next(get_db())
            try:
                conversation_service = ConversationService(db)

                # Create message in database
                message_create = MessageCreate(
                    content=text,
                    user_id=user_id,
                    user_name=user_name,
                    platform=PlatformType.TEAMS,
                    channel_id=channel_id,
                    thread_id=conversation_id
                )

                message_response = await conversation_service.add_message(message_create)

                # Check if we should trigger diagram generation
                if message_response.is_technical and \
                   message_response.confidence_score >= settings.TECHNICAL_CONFIDENCE_THRESHOLD:

                    # Check if we should generate diagram
                    should_generate = await conversation_service.should_generate_diagram(
                        message_response.conversation_id
                    )

                    if should_generate:
                        await self._trigger_diagram_generation(
                            turn_context,
                            message_response.conversation_id,
                            conversation_service,
                            db
                        )

            finally:
                db.close()

        except Exception as e:
            logger.error(f"Error processing message: {e}")
            await turn_context.send_activity(
                MessageFactory.text("Sorry, I encountered an error processing your message.")
            )

    async def _handle_bot_command(
        self,
        turn_context: TurnContext,
        text: str,
        user_id: str,
        user_name: str
    ):
        """Handle bot commands"""
        # Remove @mention
        command = text.replace("@DiagramBot", "").replace("<at>DiagramBot</at>", "").strip()
        command_lower = command.lower()

        if command_lower == "status":
            await self._handle_status_command(turn_context)

        elif command_lower == "generate":
            await self._handle_generate_command(turn_context, user_id, user_name)

        elif command_lower.startswith("modify"):
            modification_text = command[6:].strip()
            await self._handle_modify_command(turn_context, modification_text, user_id)

        elif command_lower in ["help", ""]:
            await self._handle_help_command(turn_context)

        else:
            await turn_context.send_activity(
                MessageFactory.text(
                    f"Unknown command: {command}. Type '@DiagramBot help' for available commands."
                )
            )

    async def _handle_status_command(self, turn_context: TurnContext):
        """Handle status command"""
        channel_id = self._get_channel_id(turn_context)
        conversation_id = turn_context.activity.conversation.id

        db = next(get_db())
        try:
            conversation_service = ConversationService(db)

            # Get or create conversation
            conversation = await conversation_service.get_or_create_conversation(
                platform=PlatformType.TEAMS,
                channel_id=channel_id,
                thread_id=conversation_id
            )

            # Get technical messages
            technical_messages = await conversation_service.get_technical_messages(
                conversation.id,
                time_window_minutes=settings.CONVERSATION_TIME_WINDOW_MINUTES
            )

            status_message = (
                f"**Detection Status**\n\n"
                f"- Technical messages detected: {len(technical_messages)}\n"
                f"- Conversation ID: {conversation.id}\n"
                f"- Time window: {settings.CONVERSATION_TIME_WINDOW_MINUTES} minutes\n"
                f"- Confidence threshold: {settings.TECHNICAL_CONFIDENCE_THRESHOLD}\n\n"
            )

            if len(technical_messages) >= 3:
                status_message += "✅ Ready for diagram generation!"
            else:
                status_message += f"⏳ Need {3 - len(technical_messages)} more technical messages"

            await turn_context.send_activity(MessageFactory.text(status_message))

        finally:
            db.close()

    async def _handle_generate_command(
        self,
        turn_context: TurnContext,
        user_id: str,
        user_name: str
    ):
        """Handle generate command"""
        channel_id = self._get_channel_id(turn_context)
        conversation_id = turn_context.activity.conversation.id

        db = next(get_db())
        try:
            conversation_service = ConversationService(db)

            # Get or create conversation
            conversation = await conversation_service.get_or_create_conversation(
                platform=PlatformType.TEAMS,
                channel_id=channel_id,
                thread_id=conversation_id
            )

            await self._trigger_diagram_generation(
                turn_context,
                conversation.id,
                conversation_service,
                db
            )

        finally:
            db.close()

    async def _handle_modify_command(
        self,
        turn_context: TurnContext,
        modification_text: str,
        user_id: str
    ):
        """Handle modify command"""
        if not modification_text:
            await turn_context.send_activity(
                MessageFactory.text("Please provide modification instructions. Example: @DiagramBot modify Add Redis cache")
            )
            return

        # Get latest diagram for this conversation
        channel_id = self._get_channel_id(turn_context)
        conversation_id = turn_context.activity.conversation.id

        db = next(get_db())
        try:
            conversation_service = ConversationService(db)
            diagram_service = DiagramService(db)

            # Get conversation
            conversation = await conversation_service.get_or_create_conversation(
                platform=PlatformType.TEAMS,
                channel_id=channel_id,
                thread_id=conversation_id
            )

            # Get latest diagram
            latest_diagram = await diagram_service.get_latest_diagram(conversation.id)

            if not latest_diagram:
                await turn_context.send_activity(
                    MessageFactory.text("No diagram found. Generate one first using '@DiagramBot generate'")
                )
                return

            # Modify diagram
            await turn_context.send_activity(
                MessageFactory.text("🔄 Modifying diagram...")
            )

            from backend.api.models.schemas import ModificationRequest
            modification = ModificationRequest(
                diagram_id=latest_diagram.id,
                request=modification_text,
                user_id=user_id
            )

            result = await diagram_service.modify_diagram(modification)

            if result.success:
                # Send adaptive card with new diagram
                await self._send_diagram_card(
                    turn_context,
                    result.new_diagram,
                    "Diagram Modified Successfully"
                )
            else:
                await turn_context.send_activity(
                    MessageFactory.text(f"❌ Failed to modify diagram: {result.error_message}")
                )

        finally:
            db.close()

    async def _handle_help_command(self, turn_context: TurnContext):
        """Handle help command"""
        help_text = """
**Architecture Diagram Bot - Commands**

- `@DiagramBot status` - Show current detection status
- `@DiagramBot generate` - Force diagram generation from recent messages
- `@DiagramBot modify [description]` - Request diagram modifications
- `@DiagramBot help` - Show this help message

**How it works:**
1. I monitor your conversations for technical/architectural discussions
2. When I detect enough technical content, I automatically generate diagrams
3. You can view, edit, and download diagrams through the web interface
4. Diagrams are generated in PlantUML and Draw.io formats with PNG previews
"""
        await turn_context.send_activity(MessageFactory.text(help_text))

    async def _trigger_diagram_generation(
        self,
        turn_context: TurnContext,
        conversation_db_id: int,
        conversation_service: ConversationService,
        db
    ):
        """Trigger diagram generation"""
        try:
            # Notify user
            await turn_context.send_activity(
                MessageFactory.text("🎨 I've detected an architecture discussion! Generating diagram...")
            )

            # Get conversation context
            context = await conversation_service.get_conversation_context(
                conversation_db_id
            )

            if not context:
                await turn_context.send_activity(
                    MessageFactory.text("Not enough technical messages to generate diagram.")
                )
                return

            # Generate diagram
            diagram_service = DiagramService(db)
            diagram = await diagram_service.generate_diagram(
                conversation_db_id,
                context
            )

            # Send adaptive card with diagram
            await self._send_diagram_card(
                turn_context,
                diagram,
                "Architecture Diagram Generated"
            )

        except Exception as e:
            logger.error(f"Error generating diagram: {e}")
            await turn_context.send_activity(
                MessageFactory.text(f"❌ Failed to generate diagram: {str(e)}")
            )

    async def _send_diagram_card(
        self,
        turn_context: TurnContext,
        diagram,
        title: str
    ):
        """Send adaptive card with diagram information"""
        # Create adaptive card
        card = {
            "type": "AdaptiveCard",
            "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
            "version": "1.4",
            "body": [
                {
                    "type": "TextBlock",
                    "text": title,
                    "weight": "Bolder",
                    "size": "Large"
                },
                {
                    "type": "FactSet",
                    "facts": [
                        {
                            "title": "Diagram ID:",
                            "value": str(diagram.id)
                        },
                        {
                            "title": "Version:",
                            "value": str(diagram.version)
                        },
                        {
                            "title": "Components:",
                            "value": str(diagram.components_count)
                        },
                        {
                            "title": "Relationships:",
                            "value": str(diagram.relationships_count)
                        }
                    ]
                },
                {
                    "type": "TextBlock",
                    "text": "View and edit your diagram in the web application:",
                    "wrap": True
                }
            ],
            "actions": [
                {
                    "type": "Action.OpenUrl",
                    "title": "View Diagram",
                    "url": f"http://localhost:3000/diagrams/{diagram.id}"
                },
                {
                    "type": "Action.OpenUrl",
                    "title": "Download PNG",
                    "url": f"http://localhost:8000/api/v1/diagrams/{diagram.id}/png"
                }
            ]
        }

        # Create attachment
        attachment = {
            "contentType": "application/vnd.microsoft.card.adaptive",
            "content": card
        }

        # Send message with card
        message = MessageFactory.attachment(attachment)
        await turn_context.send_activity(message)

    def _get_channel_id(self, turn_context: TurnContext) -> str:
        """Extract channel ID from turn context"""
        if hasattr(turn_context.activity, 'channel_data'):
            channel_data = turn_context.activity.channel_data
            if channel_data and 'channel' in channel_data:
                return channel_data['channel'].get('id')

        return turn_context.activity.conversation.id

    async def on_members_added_activity(
        self,
        members_added: list[ChannelAccount],
        turn_context: TurnContext
    ):
        """Handle bot added to conversation"""
        for member in members_added:
            if member.id != turn_context.activity.recipient.id:
                welcome_message = (
                    "👋 Hello! I'm the Architecture Diagram Bot.\n\n"
                    "I automatically detect technical and architectural discussions in your "
                    "conversations and generate editable diagrams.\n\n"
                    "Just chat naturally about your system architecture, and I'll create "
                    "diagrams for you!\n\n"
                    "Type '@DiagramBot help' to see available commands."
                )
                await turn_context.send_activity(MessageFactory.text(welcome_message))
