"""This module is used to crawl the area data of 51job."""

import re
import sqlite3

import requests
from fake_useragent import UserAgent

from spider import logger
from spider.config import SQLITE_FILE_PATH


class AreaSpider51:
    """This crawler is crawled based on the API."""

    def __init__(self):
        """Init the url param."""
        self.url = "https://js.51jobcdn.com/in/js/h5/dd/d_jobarea.js"
        self.user_agent = UserAgent().random
        self.headers = {
            "User-Agent": self.user_agent,
        }

    def get_data_list(self):
        """Get area list data."""
        try:
            response = requests.get(self.url, headers=self.headers)
            response.raise_for_status()
        except requests.RequestException as e:
            logger.error(f"Failed to get data: {e}")
            return []

        data = response.text
        hotcity_start = data.find("hotcity") + 8
        hotcity_end = data.find("]", hotcity_start)
        hotcity = data[hotcity_start : hotcity_end + 1]

        allProvince_start = data.find("allProvince") + 12
        allProvince_end = data.find("]", allProvince_start)
        allProvince = data[allProvince_start : allProvince_end + 1]

        combined_data = (hotcity + allProvince).replace("][", ",")
        pattern = r'{k:"(.*?)",v:"(.*?)"}'
        areaTupleList = re.findall(pattern, combined_data)
        return areaTupleList

    def save(self, data: list):
        """Save functions through different types of mappings."""
        self.save_to_db(data, SQLITE_FILE_PATH)

    def save_to_db(self, data: list, output: str):
        """Save list data to sqlite."""
        sqlClean = """DROP TABLE IF EXISTS `area51`;"""

        sqlTable = """CREATE TABLE IF NOT EXISTS `area51` (
                  `code` VARCHAR(10) NOT NULL,
                  `area` VARCHAR(10) NOT NULL,
                  PRIMARY KEY (`code`)
        );"""

        sql = """INSERT INTO `area51` VALUES(?, ?);"""

        try:
            with sqlite3.connect(output) as connect:
                cursor = connect.cursor()
                cursor.execute(sqlClean)
                cursor.execute(sqlTable)
                cursor.executemany(sql, data)
                connect.commit()
        except Exception as e:
            logger.warning("SQL execution failure of SQLite: " + str(e))


def start():
    """Spider starter."""
    spider = AreaSpider51()
    data = spider.get_data_list()

    if data is None:
        logger.warning("No data to save")
        return

    logger.info(f"Saving {len(data)} items to {SQLITE_FILE_PATH}")
    spider.save(data)
