"""Main function of the project."""
import sqlite3

import pandas as pd

from spider import jobspider51, logger
from spider.area import areaspider51


def area():
    """Get all area code."""
    areaspider51.start(save_engine="csv")
    logger.close()


def part_spider():
    """Get the data of Job."""
    param = {"keyword": "Python", "page": 1, "area": "000000"}
    jobspider51.start(args=param, save_engine="both")
    logger.close()


def full_job_spider(save_engine: str, pageNum: int = 20):
    """Get the data of Job."""
    save_to = {
        "csv": lambda x: full_spider_csv(x),
        "db": lambda x: full_spider_db(x, pageNum),
        "both": lambda x: full_spider_csv(x),
    }
    save = save_to[save_engine]
    save(save_engine)
    logger.close()


def full_spider_csv(type: str):
    """Get the data of Job save to csv."""
    df = pd.read_csv(
        "../output/area/51area.csv",
        header=None,
        names=None,
        skiprows=1,
        delimiter=",",
    )

    for area in df[0]:
        param = {"keyword": "Python", "page": 1, "area": area}
        jobspider51.start(args=param, save_engine=type)

    logger.close()


def full_spider_db(type: str, pageNum: int):
    """Get the data of Job save to db."""
    results = None
    connect = sqlite3.connect("output/area/51area.db")
    cursor = connect.cursor()
    sql = """SELECT `code`, `area` FROM `area51`;"""
    try:
        cursor.execute(sql)
        results = cursor.fetchall()
        connect.commit()
    except Exception as e:
        logger.warning("SQL execution failure of SQLite: " + str(e))
    finally:
        cursor.close()
        connect.close()

    for area in results[STRAT_AREA_CODE - 1 : END_AREA_CODE]:
        for page in range(1, pageNum + 1):
            param = {"keyword": KEYWORD, "page": page, "area": area[0]}
            logger.info(f"Crawling area {area[0]}-{area[1]} of page-{page}")
            jobspider51.start(args=param, save_engine=type)


KEYWORD = "数据挖掘"

# The maximum value of total result is 1000,
# one page return 50 results, and the maximum page is 20
MAX_PAGE_NUM = 20

# control the area, total is 56.
STRAT_AREA_CODE = 24
END_AREA_CODE = 30

if __name__ == "__main__":
    # area()
    # TODO: DB works well, but CSV still has some problem.
    full_job_spider(save_engine="db", pageNum=MAX_PAGE_NUM)
    logger.close()
