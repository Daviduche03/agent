from dotenv import load_dotenv

from livekit import agents
from livekit.agents import (
    AgentSession,
    function_tool,
    Agent,
    RunContext,
    RoomInputOptions,
    RoomOutputOptions,
)
from livekit.plugins import (
    openai,
    noise_cancellation,
    google,
)
from openai.types.beta.realtime.session import TurnDetection
from prompt import getAgentDetails
import logging

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Assistant(Agent):
    def __init__(self) -> None:
        super().__init__(instructions="systemPrompt")


async def entrypoint(ctx: agents.JobContext):
    await ctx.connect()

    @function_tool()
    async def lookup_user(
        context: RunContext,
        user_id: str,
    ) -> dict:
        """Look up a user's information by ID."""
        return {"name": "John Doe", "email": "john.doe@example.com"}

    participant = await ctx.wait_for_participant()
    logger.info(f"Starting voice assistant for participant {participant.identity}")

    systemPrompt = getAgentDetails(participant.identity)

    session = AgentSession(
        llm=google.beta.realtime.RealtimeModel(
            model="gemini-2.0-flash-exp",
            voice="Puck",
            temperature=0.6,
            instructions=systemPrompt,
        ),
    )

    await session.start(
        room=ctx.room,
        agent=Assistant(),
        room_input_options=RoomInputOptions(
            noise_cancellation=noise_cancellation.BVC(),
            video_enabled=True,
        ),
        room_output_options=RoomOutputOptions(transcription_enabled=True),
    )

    await session.generate_reply(
        instructions="Greet the user and offer your assistance."
    )


if __name__ == "__main__":
    agents.cli.run_app(agents.WorkerOptions(entrypoint_fnc=entrypoint))
