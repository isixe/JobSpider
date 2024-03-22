"""Main function of the project."""

import asyncio
import random
from pathlib import Path

from spider import areaspider51, areaspiderboss, jobspider51, jobspiderboss, logger
from utility.constant import (
    KEYWORD,
    MAX_51PAGE_NUM,
    MAX_ASY_NUM,
)
from utility.path import (
    AREA51_SQLITE_FILE_PATH,
    AREABOSS_SQLITE_FILE_PATH,
)
from utility.sql import execute_sql_command


def area51_spider() -> None:
    """Get all area code."""
    areaspider51.start()


def job51_spider(page_num: int = MAX_51PAGE_NUM) -> None:
    """Get the data of Job."""
    if not Path.exists(AREA51_SQLITE_FILE_PATH):
        area51_spider()

    areas = execute_sql_command(
        """SELECT `code`, `area` FROM `area51`;""", AREA51_SQLITE_FILE_PATH
    )
    if not areas:
        msg = "Please get areas first."
        raise ValueError(msg)

    for area in areas:
        for page in range(1, page_num + 1):
            param = {"keyword": KEYWORD, "page": page, "area": area[0]}
            logger.info(f"Crawling area-{area[1]} of page-{page}")
            jobspider51.start(args=param)


def areaboss_spider() -> None:
    """Get all area code."""
    areaspiderboss.start()


async def joboss_max_page_spider(areas: list[tuple[str]]) -> None:
    """Get the max page of Joboss."""
    jobspiderboss.create_joboss_max_page_table()

    while areas:
        selected_areas = [
            areas.pop(areas.index(random.choice(areas)))
            for _ in range(min(MAX_ASY_NUM, len(areas)))
        ]

        await asyncio.gather(  # could be rewritten with TaskGroup
            *[
                jobspiderboss.update_page(keyword=KEYWORD, area_code=area[0])
                for area in selected_areas
            ]
        )


async def joboss_read_areas() -> list[tuple[str]]:
    """Get areas from the database."""
    query = """SELECT `code`, `name` FROM `areaboss`;"""
    result = execute_sql_command(query, AREABOSS_SQLITE_FILE_PATH)
    if result:
        return result
    return []


async def joboss_spider() -> None:
    """Get the data of Job."""
    if not Path(AREABOSS_SQLITE_FILE_PATH).exists():
        areaboss_spider()

    areas = await joboss_read_areas()
    if areas and not jobspiderboss.check_joboss_max_page_table():
        await joboss_max_page_spider(areas)

    if not jobspiderboss.check_joboss_url_pool_table():
        jobspiderboss.build_url_pool()

    await jobspiderboss.crawl_many()


if __name__ == "__main__":
    asyncio.run(joboss_spider())
    logger.close()
