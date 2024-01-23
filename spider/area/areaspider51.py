"""This module is used to crawl the area data of 51job."""
import os
import re
import sqlite3
import ssl

import pandas as pd
import requests
import urllib3
from fake_useragent import UserAgent

from spider import logger


# Due to the limitations of the '51job' interface,
# the maximum number of entries that can be obtained per search term is limited to 1000
class AreaSpider51:
    """This crawler is crawled based on the API."""

    def __init__(self):
        """Init the url param."""
        self.url = "https://js.51jobcdn.com/in/js/h5/dd/d_jobarea.js"
        self.user_agent = UserAgent().random
        self.headers = {
            "User-Agent": self.user_agent,
        }
        self.CSV_FILE = "51area.csv"
        self.SQLITE_FILE = "51area.db"
        self.create_output_dir()

    def get_data_list(self):
        """Get area list data.

        The following is the execution order

            Get row data by request
            String processing
            Extract by regular expression

        Finally, return list data
        """
        request = get_legacy_session().get(self.url, headers=self.headers).text
        start = request.find("hotcity") + 8
        end = request.find("]", start)
        hotcity = request[start : end + 1]

        start = request.find("allProvince") + 12
        end = request.find("]", start)
        allProvince = request[start : end + 1]
        data = (hotcity + allProvince).replace("][", ",")
        areaList = data[1:-1]

        pattern = r'{k:"(.*?)",v:"(.*?)"}'
        areaTupleList = re.findall(pattern, areaList)
        areaTupleList.pop(0)
        return areaTupleList

    @staticmethod
    def create_output_dir():
        """Create output directory if not exists."""
        root = os.path.abspath("..")
        directory = os.path.join(root, "output/area")
        if not os.path.exists(directory):
            os.makedirs(directory)

    def save(self, data: list, type: str):
        """Save functions through different types of mappings.

        :Arg:
         - data: City List
         - type: Data storage engine, support for csv, db and both
        """
        root = os.path.abspath("..")
        CSV_FILE_PATH = os.path.join(root, "output/area/" + self.CSV_FILE)
        SQLITE_FILE_PATH = os.path.join(root, "output/area/" + self.SQLITE_FILE)

        save_to = {
            "csv": lambda x: self.save_to_csv(x, CSV_FILE_PATH),
            "db": lambda x: self.save_to_db(x, SQLITE_FILE_PATH),
            "both": lambda x: (
                self.save_to_csv(x, CSV_FILE_PATH),
                self.save_to_db(x, SQLITE_FILE_PATH),
            ),
        }
        save = save_to[type]
        save(data)

    def save_to_csv(self, data: list, output: str):
        """Save list data to csv.

        :Arg:
         - data: City List
         - output: Data output path
        """
        label = ["code", "area"]
        df = pd.DataFrame(data, columns=["k", "v"])
        df.to_csv(output, index=False, header=label, encoding="utf-8")

    def save_to_db(self, data: list, output: str):
        """Save list data to sqlite.

        :Arg:
         - data: City List
         - output: Data output path
        """
        connect = sqlite3.connect(output)
        cursor = connect.cursor()
        sqlClean = """DROP TABLE IF EXISTS `area51`;"""

        sqlTable = """CREATE TABLE IF NOT EXISTS `area51` (
                  `code` VARCHAR(10) NOT NULL,
                  `area` VARCHAR(10) NOT NULL,
                  PRIMARY KEY (`code`)
        );"""

        sql = """INSERT INTO `area51` VALUES(?, ?);"""

        try:
            cursor.execute(sqlClean)
            cursor.execute(sqlTable)
            cursor.executemany(sql, data)
            connect.commit()
        except Exception as e:
            logger.warning("SQL execution failure of SQLite: " + str(e))
        finally:
            cursor.close()
            connect.close()


class CustomHttpAdapter(requests.adapters.HTTPAdapter):
    """Transport adapter" that allows us to use custom ssl_context."""

    # ref: https://stackoverflow.com/a/73519818/16493978

    def __init__(self, ssl_context=None, **kwargs):
        """Init the ssl_context param."""
        self.ssl_context = ssl_context
        super().__init__(**kwargs)

    def init_poolmanager(self, connections, maxsize, block=False):
        """Create a urllib3.PoolManager for each proxy."""
        self.poolmanager = urllib3.poolmanager.PoolManager(
            num_pools=connections,
            maxsize=maxsize,
            block=block,
            ssl_context=self.ssl_context,
        )


def get_legacy_session():
    """Get legacy session."""
    ctx = ssl.create_default_context(ssl.Purpose.SERVER_AUTH)
    ctx.options |= 0x4  # OP_LEGACY_SERVER_CONNECT
    session = requests.session()
    session.mount("https://", CustomHttpAdapter(ctx))
    return session


def start(save_engine: str):
    """Spider starter.

    :Arg:
     - save_engine: Data storage engine, support for csv, db and both
    """
    if save_engine not in ["csv", "db", "both"]:
        return logger.error("The data storage engine must be 'csv' , 'db' or 'both' ")

    spider = AreaSpider51()
    data = spider.get_data_list()
    spider.save(data, save_engine)
