"""There are some utility functions for path operations."""

from pathlib import Path

from spider import logger


def create_output_dir(tag: str) -> str:
    """Create output directory if not exists."""
    root = Path(__file__).resolve().parent.parent
    directory = root / f"output/{tag}"

    if not directory.exists():
        directory.mkdir(parents=True)
        logger.debug(f"Directory {directory} created.")
    else:
        logger.debug(f"Directory {directory} already exists.")
    return str(directory)


AREA51_SQLITE_FILE_PATH = Path(create_output_dir(tag="area")) / "51area.db"
JOB51_SQLITE_FILE_PATH = Path(create_output_dir(tag="job")) / "51job.db"

JOBOSS_SQLITE_FILE_PATH = Path(create_output_dir(tag="job")) / "bossjob.db"
AREABOSS_SQLITE_FILE_PATH = Path(create_output_dir(tag="area")) / "bossarea.db"

BOSS_COOKIES_FILE_PATH = Path(create_output_dir(tag="cookies")) / "BossCookies.json"
