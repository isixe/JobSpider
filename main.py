"""Main function of the project."""

import sqlite3
from pathlib import Path

from spider import areaspider51, jobspider51, logger

AREA_DB_PATH = Path(__file__).resolve().parent / "output" / "area" / "51area.db"
MAX_PAGE_NUM = 20
STRAT_AREA_CODE = 1
END_AREA_CODE = None
KEYWORD = "数据挖掘"


def area_spider() -> None:
    """Get all area code."""
    areaspider51.start()


def job_spider(page_num: int = MAX_PAGE_NUM) -> None:
    """Get the data of Job."""
    if not Path.exists(AREA_DB_PATH):
        area_spider()
    job_spider_db(page_num)


def job_spider_db(page_num: int) -> None:
    """Get the data of Job save to db."""
    results = None

    sql = """SELECT `code`, `area` FROM `area51`;"""
    try:
        with sqlite3.connect(AREA_DB_PATH) as connect:
            cursor = connect.cursor()
            cursor.execute(sql)
            results = cursor.fetchall()
    except sqlite3.Error as e:
        logger.warning(f"SQL execution failure of SQLite: {e!s}")

    for area in results[STRAT_AREA_CODE - 1 : END_AREA_CODE]:
        for page in range(1, page_num + 1):
            param = {"keyword": KEYWORD, "page": page, "area": area[0]}
            logger.info(f"Crawling area-{area[1]} of page-{page}")
            jobspider51.start(args=param)


if __name__ == "__main__":
    job_spider()
    logger.close()
