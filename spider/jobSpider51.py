# !/usr/bin/env python
# -*-coding:utf-8 -*-
# @Time    : 2023/10/31 10:36
# @Author  : isixe
# @Version : python3.10.6
# @Desc    : job data spider

import os
import random
import re
import json
import time
import sqlite3
import pandas as pd
from log import handlerLogger
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver import ActionChains
from selenium.webdriver.common.by import By

logger = handlerLogger.HandlerLogger(filename='spider.log')


class JobSipder51(object):
    """ This crawler is crawled based on the API"""

    def __init__(self, keyword: str, page: int, pageSize: int, city: str):
        """ Init the url param

        :Args:
         - keyword: Search keyword
         - page: Page number
         - pageSize: Specify the number of data per page
         - city: Specify the city to search for
        """
        self.keyword = keyword
        self.page = page
        self.pageSize = pageSize
        self.city = city
        self.baseUrl = ('https://we.51job.com/api/job/search-pc?api_key=51job&searchType=2&function=&industry='
                        '&jobArea2=&landmark=&metro=&salary=&workYear=&degree=&companyType=&companySize=&jobType='
                        '&issueDate=&sortType=0&pageNum=1&requestId=&source=1&accountId=&pageCode=sou%7Csou%7Csoulb')
        self.CSV_FILE = '51job.csv'
        self.SQLITE_FILE = '51job.db'
        self.create_output_dir()

    @staticmethod
    def create_output_dir():
        """ Create output directory if not exists """
        root = os.path.abspath('..')

        directory = os.path.join(root, "output")
        if not os.path.exists(directory):
            os.makedirs(directory)

    def get_data_json(self):
        """ Get job JSON data

        The following is the execution order

            Driver building and start url
            Passing slider verification
            Getting HTML source
            Parsing HTML by BeautifulSoup, obtain the data through the first div
            Json Parsing

        Finally, return json data
        """

        extra = f"&keyword={self.keyword}&pageSize={self.pageSize}&jobArea={self.city}"
        url = self.baseUrl + extra
        web = self.driver_builder()

        dataJson = None
        while (True):
            try:
                web.get(url)

                time.sleep(1)
                self.slider_verify(web)
                time.sleep(2)

                html = web.page_source
                soup = BeautifulSoup(html, "html.parser")
                data = soup.find('div').text

                dataJson = json.loads(data)
                dataJson = dataJson['resultbody']['job']['items']
                break
            except:
                logger.warning("data json sipder failed, waiting for try again")
            finally:
                web.close()
        return dataJson

    def driver_builder(self):
        """ Init webdriver

        During the building process, it is necessary to set up an anti crawler detection strategy by Option.

            .add_argument('headless')
            -> Set headless page, run silently

            .add_argument("--window-size=1920,1080")
            -> In headless status, browse without a window size, so if the size of the window is not specified,
            sliding verification may fail

            .add_experimental_option('excludeSwitches',['enable-automation','enable-logging'])
            -> Disable auto control and log feature of the browser

            .add_argument('--disable-blink-features=AutomationControlled')
            -> Set navigator.webdriver=false

            .add_argument('--disable-blink-features=AutomationControlled')
            -> Disable auto control extension of the browser

        Additionally, if use the visible window execution, you need to add the following operations

            .add_argument('--inprivate')
            -> Start by Private Browsing

            .add_argument("--start-maximized")
            -> Maximize the window

        Finally, inject script to change navigator = false.
        """

        options = webdriver.EdgeOptions()
        options.add_argument('headless')
        options.add_argument("--window-size=1920,1080")

        options.add_experimental_option('excludeSwitches', ['enable-automation', 'enable-logging'])
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_experimental_option('useAutomationExtension', False)
        # options.add_argument('--inprivate')
        # options.add_argument("--start-maximized")

        web = webdriver.Edge(options=options)

        script = 'Object.defineProperty(navigator, "webdriver", {get: () => false,});'
        web.execute_script(script)
        return web

    def slider_verify(self, web: webdriver):
        """ Slider verification action

        This requires the mouse to perform the following operations in following order

            1. put mouse on slider       ->   .move_to_element(slider)
            2. hold mouse on             ->   .click_and_hold()
            3. move to target position   ->   .move_by_offset(300, 0)

        Finally, perform action          ->   .perform()
        """
        slider = web.find_elements(By.XPATH, '//div[@class="nc_bg"]')

        if len(slider) <= 0:
            logger.warning("slider not found")
            return

        slider = slider[0]
        action_chains = (ActionChains(web)
                         .move_to_element(slider)
                         .click_and_hold()
                         .move_by_offset(300 + random.randint(1, 20), 0))

        action_chains.perform()

    def save(self, items: json, type: str):
        """ Iterate through the dictionary to get each item, save each data by specify type.

        Otherwise, the process will try to crawl work requirements and work position.
        If crawl failed, it is set empty and skip after three retries.

        Finally, add column header and remove duplicate rows
        """
        root = os.path.abspath('..')
        CSV_FILE_PATH = os.path.join(root, "output/" + self.CSV_FILE)
        SQLITE_FILE_PATH = os.path.join(root, "output/" + self.SQLITE_FILE)

        save_to = {
            'csv': lambda x: self.save_to_csv(x, CSV_FILE_PATH),
            'db': lambda x: self.save_to_db(x, SQLITE_FILE_PATH)
        }

        for key, item in enumerate(items):
            logger.info('processing in item' + str(key + 1))

            jobDetailDict = {
                'jobName': item['jobName'],
                'tags': ",".join(item['jobTags']),
                'city': ''.join(re.findall(r'[\u4e00-\u9fa5]+', str(item['jobAreaLevelDetail']))),
                'salary': item['provideSalaryString'],
                'workYear': item['workYearString'],
                'degree': item['degreeString'],
                'jobRequire': '',
                'companyName': item['fullCompanyName'],
                'companyType': item['companyTypeString'],
                'companySize': item['companySizeString'],
                'workAddress': '',
                'logo': item['smallHrLogoUrl'],
                'issueDate': item['issueDateString']
            }

            web = self.driver_builder()
            count = 3
            while (count >= 0):
                try:
                    web.get(item['jobHref'])

                    time.sleep(1)
                    self.slider_verify(web)
                    time.sleep(3)

                    jobRequire = web.find_element(By.XPATH, '//div[@class="bmsg job_msg inbox"]').text
                    workAddress = web.find_element(By.XPATH, '//div[@class="bmsg inbox"]/p[@class="fp"]').text
                    jobDetailDict['jobRequire'] = jobRequire
                    jobDetailDict['workAddress'] = workAddress
                    break
                except:
                    count = count - 1
                    logger.warning("web element spider failed, waiting for try again. retry count: " + str(count + 1))
                    break
                finally:
                    web.close()

            save = save_to[type]
            save(jobDetailDict)

        if type == 'csv':
            label = (['职位名称', '标签', '城市', '薪资', '工作年限', '学位要求',
                      '工作要求', '公司名称', '公司类型', '人数', '工作地址', 'Logo', '发布时间'])

            header = pd.read_csv(CSV_FILE_PATH, nrows=0).columns.tolist()
            names, set_header = None, False
            if not set(label).intersection(header):
                names = label
                set_header = True

            df = pd.read_csv(CSV_FILE_PATH, header=None, names=names, delimiter=',')
            df.drop_duplicates(inplace=True)
            df.to_csv(CSV_FILE_PATH, index=False, header=set_header)

    def save_to_csv(self, detail: dict, output: str):
        """ Save dict data to csv """

        detail = [v for k, v in enumerate(detail.values())]
        df = pd.DataFrame([detail])
        df.to_csv(output, index=False, header=False, mode='a')

    def save_to_db(self, detail: dict, output: str):
        """ Save dict data to sqlite """
        connect = sqlite3.connect(output)
        cursor = connect.cursor()
        sql_table = ('''CREATE TABLE IF NOT EXISTS `job51` (
                  `jobName` VARCHAR(255) NOT NULL,
                  `tags` VARCHAR(255) NULL,
                  `city` VARCHAR(50) NULL,
                  `salary` VARCHAR(255) NULL,
                  `workYear` VARCHAR(10) NULL,
                  `degree` VARCHAR(10) NULL,
                  `jobRequire` VARCHAR(255) NULL,
                  `companyName` VARCHAR(255) NULL,
                  `companyType` VARCHAR(255) NULL,
                  `companySize` VARCHAR(10) NULL,
                  `workAddress` VARCHAR(255) NULL,
                  `logo` VARCHAR(255) NULL,
                  `issueDate` VARCHAR(50) NULL,
                  PRIMARY KEY (`jobName`,`city`)
        );''')

        sql = '''INSERT INTO `job51` VALUES(
            :jobName,
            :tags,
            :city,
            :salary,
            :workYear,
            :degree,
            :jobRequire,
            :companyName,
            :companyType,
            :companySize,
            :workAddress,
            :logo,
            :issueDate
        );'''

        try:
            cursor.execute(sql_table)
            cursor.execute(sql, detail)
            connect.commit()
        except:
            logger.warning("SQL execution failure of SQLite")
        finally:
            cursor.close()
            connect.close()


def start(args: dict, save_engine: str):
    """ spider starter

    :Args:
     - param: Url param, type Dict{'keyword': str, 'page': int, 'pageSize': int, 'city': str}
     - save_engine: data storage engine, support for csv or db
    """
    if save_engine not in ['csv', 'db']:
        return logger.critical("The data storage engine must be 'csv' or 'db'")

    spider = JobSipder51(keyword=args['keyword'], page=args['page'], pageSize=args['pageSize'], city=args['city'])
    json = spider.get_data_json()
    spider.save(json, save_engine)


if __name__ == '__main__':
    param = {
        "keyword": "前端",
        "page": 10,
        "pageSize": 50,
        "city": "000000"
    }
    start(args=param, save_engine='db')
