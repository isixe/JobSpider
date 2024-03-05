"""Utility functions for the spider."""

from pathlib import Path

from spider import logger

# ref: https://stackoverflow.com/a/73519818/16493978


def create_output_dir(tag: str) -> str:
    """Create output directory if not exists."""
    root = Path(__file__).resolve().parent.parent
    directory = root / f"output/{tag}"

    if not directory.exists():
        directory.mkdir(parents=True)
        logger.info(f"Directory {directory} created.")
    else:
        logger.info(f"Directory {directory} already exists.")
    return str(directory)
