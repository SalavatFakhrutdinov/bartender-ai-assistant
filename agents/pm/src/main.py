"""PM Agent entrypoint."""

import asyncio

from shared.logging import configure_logging
from src.pm import PMAgent


async def main() -> None:
    configure_logging()
    agent = PMAgent()
    await agent.start()

    try:
        while True:
            await asyncio.sleep(1)
    except asyncio.CancelledError:
        pass
    finally:
        await agent.stop()


if __name__ == "__main__":
    asyncio.run(main())
