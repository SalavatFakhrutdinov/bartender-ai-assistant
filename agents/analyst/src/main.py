"""Analyst Agent entrypoint."""

import asyncio

from shared.logging import configure_logging
from agents.analyst.src.analyst import AnalystAgent


async def main() -> None:
    configure_logging()
    agent = AnalystAgent()
    await agent.start()

    # Keep running
    try:
        while True:
            await asyncio.sleep(1)
    except asyncio.CancelledError:
        pass
    finally:
        await agent.stop()


if __name__ == "__main__":
    asyncio.run(main())
