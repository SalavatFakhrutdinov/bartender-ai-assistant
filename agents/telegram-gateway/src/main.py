"""Telegram Gateway entrypoint."""

import asyncio
import sys
from pathlib import Path

# Allow imports from this src directory
sys.path.insert(0, str(Path(__file__).parent))

from shared.logging import configure_logging
from bot import TelegramBot


async def main() -> None:
    configure_logging()
    bot = TelegramBot()
    await bot.setup()
    await bot.run()

    # Keep running until interrupted
    try:
        while True:
            await asyncio.sleep(1)
    except asyncio.CancelledError:
        pass
    finally:
        await bot.stop()


if __name__ == "__main__":
    asyncio.run(main())
