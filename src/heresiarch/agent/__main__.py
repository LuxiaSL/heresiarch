"""Entry point: python -m heresiarch.agent"""

import asyncio

from heresiarch.agent.server import main

asyncio.run(main())
