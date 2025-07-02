"""
Entry point for running hierarchical-research-ai as a module
Usage: python -m hierarchical_research_ai [args]
"""

import sys
import asyncio
from .cli.interface import main

if __name__ == "__main__":
    # Enable module execution with python -m
    asyncio.run(main())