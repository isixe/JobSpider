# !/usr/bin/env python
# -*-coding:utf-8 -*-
# @Time    : 2023/12/08 10:37
# @Author  : Exisi
# @Version : python3.10.6
# @Desc    : area data spider

import os
import re
import sqlite3
import pandas as pd
import requests
from fake_useragent import UserAgent
from log import handler_logger

logger = handler_logger.HandlerLogger(filename='spider.log')


class AreaSpider51(object):
    """ This crawler is crawled based on the API"""

    def __init__(self):
        """ Init the url param """

        self.url = "https://js.51jobcdn.com/in/js/h5/dd/d_jobarea.js"
        self.user_agent = UserAgent().random
        self.headers = {
            'User-Agent': self.user_agent,
        }
        self.CSV_FILE = '51city.csv'
        self.SQLITE_FILE = '51city.db'
        self.create_output_dir()

    def get_data_list(self):
        """ Get area list data

        The following is the execution order

            Get row data by request
            String processing
            Extract by regular expression

        Finally, return list data
        """

        request = requests.get(self.url, headers=self.headers).text
        start = request.find('hotcity') + 8
        end = request.find(']', start)
        hotcity = request[start:end + 1]

        start = request.find('allProvince') + 12
        end = request.find(']', start)
        allProvince = request[start:end + 1]
        data = (hotcity + allProvince).replace("][", ",")
        cityList = data[1:-1]

        pattern = r'{k:"(.*?)",v:"(.*?)"}'
        cityTupleList = re.findall(pattern, cityList)
        cityTupleList.pop(0)
        return cityTupleList

    @staticmethod
    def create_output_dir():
        """ Create output directory if not exists """

        root = os.path.abspath('../..')
        directory = os.path.join(root, "output/city")
        if not os.path.exists(directory):
            os.makedirs(directory)

    def save(self, data: list, type: str):
        """ Save functions through different types of mappings

        :Arg:
         - data: City List
         - type: Data storage engine, support for csv, db and both
        """

        root = os.path.abspath('../..')
        CSV_FILE_PATH = os.path.join(root, "output/city/" + self.CSV_FILE)
        SQLITE_FILE_PATH = os.path.join(root, "output/city/" + self.SQLITE_FILE)

        save_to = {
            'csv': lambda x: self.save_to_csv(x, CSV_FILE_PATH),
            'db': lambda x: self.save_to_db(x, SQLITE_FILE_PATH),
            'both': lambda x: (self.save_to_csv(x, CSV_FILE_PATH),
                               self.save_to_db(x, SQLITE_FILE_PATH))
        }
        save = save_to[type]
        save(data)

    def save_to_csv(self, data: list, output: str):
        """ Save list data to csv

        :Arg:
         - data: City List
         - output: Data output path
        """
        label = (['代码', '省级行政区'])
        df = pd.DataFrame(data, columns=['k', 'v'])
        df.to_csv(output, index=False, header=label, encoding='utf-8')

    def save_to_db(self, data: list, output: str):
        """ Save list data to sqlite

        :Arg:
         - data: City List
         - output: Data output path
        """
        connect = sqlite3.connect(output)
        cursor = connect.cursor()
        sqlTable = ('''CREATE TABLE IF NOT EXISTS `area51` (
                  `code` VARCHAR(10) NOT NULL,
                  `area` VARCHAR(10) NOT NULL,
                  PRIMARY KEY (`code`)
        );''')

        sql = '''INSERT INTO `area51` VALUES(?, ?);'''

        try:
            cursor.execute(sqlTable)
            cursor.executemany(sql, data)
            connect.commit()
        except Exception as e:
            logger.warning("SQL execution failure of SQLite: " + str(e))
        finally:
            cursor.close()
            connect.close()


def start(save_engine: str):
    """ spider starter

    :Arg:
     - param: Url param, type Dict{'keyword': str, 'page': int, 'pageSize': int, 'city': str}
    """
    if save_engine not in ['csv', 'db', 'both']:
        return logger.error("The data storage engine must be 'csv' , 'db' or 'both' ")

    spider = AreaSpider51()
    data = spider.get_data_list()
    spider.save(data, save_engine)
