from aiohttp import web
from botbuilder.core import BotFrameworkAdapter, BotFrameworkAdapterSettings
from botbuilder.schema import Activity
from backend.bot.teams_bot import ArchitectureDiagramBot
from backend.config import settings
import logging

logger = logging.getLogger(__name__)

# Create adapter
adapter_settings = BotFrameworkAdapterSettings(
    app_id=settings.TEAMS_APP_ID,
    app_password=settings.TEAMS_APP_PASSWORD
)
adapter = BotFrameworkAdapter(adapter_settings)


# Error handler
async def on_error(context, error):
    logger.error(f"Bot error: {error}")
    await context.send_activity("Sorry, I encountered an error.")


adapter.on_turn_error = on_error

# Create bot
bot = ArchitectureDiagramBot()


# Message endpoint
async def messages(req: web.Request) -> web.Response:
    """Handle incoming messages from Teams"""
    if req.headers.get("Content-Type") == "application/json":
        body = await req.json()
    else:
        return web.Response(status=415)

    activity = Activity().deserialize(body)
    auth_header = req.headers.get("Authorization", "")

    try:
        response = await adapter.process_activity(activity, auth_header, bot.on_turn)
        if response:
            return web.json_response(data=response.body, status=response.status)
        return web.Response(status=201)
    except Exception as e:
        logger.error(f"Error processing activity: {e}")
        return web.Response(status=500)


# Create app
app = web.Application()
app.router.add_post("/api/messages", messages)


if __name__ == "__main__":
    web.run_app(app, host="0.0.0.0", port=3978)
