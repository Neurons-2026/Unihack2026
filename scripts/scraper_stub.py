"""Command-line stub to trigger the worker cycle without Docker.

Usage:
    python scripts/scraper_stub.py
"""
import asyncio
from backend.worker.worker import run_cycle  # type: ignore

if __name__ == "__main__":
    asyncio.run(run_cycle())
