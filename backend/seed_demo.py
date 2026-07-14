"""Run: python seed_demo.py [--replace]"""

import asyncio
import sys

from tortoise import Tortoise

from config import TORTOISE_ORM
from main import ensure_message_columns
from seed import seed_demo_messages


async def main() -> None:
    replace = "--replace" in sys.argv
    await Tortoise.init(config=TORTOISE_ORM)
    await Tortoise.generate_schemas()
    await ensure_message_columns()
    count = await seed_demo_messages(replace=replace)
    print(f"Seeded {count} demo messages (replace={replace})")
    await Tortoise.close_connections()


if __name__ == "__main__":
    asyncio.run(main())
