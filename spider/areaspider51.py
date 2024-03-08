"""This module is used to crawl the area data of 51job."""

import re
import sqlite3

import requests
from fake_useragent import UserAgent

from spider import logger
from spider.utility import AREA51_SQLITE_FILE_PATH, PLAT_CODE, get_legacy_session


class AreaSpider51:
    """This crawler is crawled based on the API."""

    def __init__(self) -> None:
        """Init the url param."""
        self.url = "https://js.51jobcdn.com/in/js/h5/dd/d_jobarea.js"
        self.user_agent = UserAgent().random
        self.headers = {
            "User-Agent": self.user_agent,
        }

    def get_data_list(self) -> list:
        """Get area list data."""
        try:
            # if in wsl/windows, should use `get_legacy_session()`
            # else use `requests.get()`
            if PLAT_CODE == 0:
                response = get_legacy_session().get(
                    self.url, headers=self.headers, timeout=10
                )
            elif PLAT_CODE == 1:
                response = requests.get(self.url, headers=self.headers, timeout=10)
            response.raise_for_status()
        except requests.RequestException as e:
            logger.error(f"Failed to get data: {e}")
            return []

        data = response.text
        hotcity_start = data.find("hotcity") + 8
        hotcity_end = data.find("]", hotcity_start)
        hotcity = data[hotcity_start : hotcity_end + 1]

        all_province_start = data.find("allProvince") + 12
        all_province_end = data.find("]", all_province_start)
        all_province = data[all_province_start : all_province_end + 1]

        combined_data = (hotcity + all_province).replace("][", ",")
        pattern = r'{k:"(.*?)",v:"(.*?)"}'
        return re.findall(pattern, combined_data)

    def save(self, data: list) -> None:
        """Save functions through different types of mappings."""
        self.save_to_db(data, AREA51_SQLITE_FILE_PATH)

    def save_to_db(self, data: list, output: str) -> None:
        """Save list data to sqlite."""
        sql_clean = """DROP TABLE IF EXISTS `area51`;"""

        sql_table = """CREATE TABLE IF NOT EXISTS `area51` (
                  `code` VARCHAR(10) NOT NULL,
                  `area` VARCHAR(10) NOT NULL,
                  PRIMARY KEY (`code`)
        );"""

        sql = """INSERT INTO `area51` VALUES(?, ?);"""

        try:
            with sqlite3.connect(output) as connect:
                cursor = connect.cursor()
                cursor.execute(sql_clean)
                cursor.execute(sql_table)
                cursor.executemany(sql, data)
                connect.commit()
        except sqlite3.Error as e:
            logger.warning("SQL execution failure of SQLite: " + str(e))


def start() -> None:
    """Spider starter."""
    spider = AreaSpider51()
    data = spider.get_data_list()

    if data is None:
        logger.warning("No data to save")
        return

    logger.info(f"Saving {len(data)} items to {AREA51_SQLITE_FILE_PATH}")
    spider.save(data)
