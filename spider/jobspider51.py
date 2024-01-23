"""This module is used to crawl 51job data."""
import json
import os
import random
import re
import sqlite3
import time

import pandas as pd
from bs4 import BeautifulSoup
from fake_useragent import UserAgent
from selenium import webdriver
from selenium.webdriver import ActionChains
from selenium.webdriver.common.by import By

from spider import logger


class JobSipder51:
    """This crawler is crawled based on the API."""

    def __init__(self, keyword: str, page: int, pageSize: int, area: str):
        """Init the url param.

        :Args:
         - keyword: Search keyword
         - page: Page number
         - pageSize: Specify the number of data per page
         - area: Specify the area to search for
        """
        self.keyword = keyword
        self.page = page
        self.pageSize = pageSize
        self.area = area
        self.timestamp = str(int(time.time()))
        self.baseUrl = (
            "https://we.51job.com/api/job/search-pc?api_key=51job&searchType=2&pageCode=sou%7Csou%7Csoulb"
            "&sortType=0&function=&industry=&landmark=&metro=&requestId=&source=1&accountId="
        )
        self.fakeUrl = "&jobArea2=&jobType=&salary=&workYear=&degree=&companyType=&companySize=&issueDate="
        self.root = os.path.abspath("..")
        self.CSV_FILE = "51job.csv"
        self.SQLITE_FILE = "51job.db"
        self.CSV_FILE_PATH = os.path.join(self.root, "output/job/" + self.CSV_FILE)
        self.SQLITE_FILE_PATH = os.path.join(
            self.root,
            "output/job/" + self.SQLITE_FILE,
        )
        self.__create_output_dir()

    @staticmethod
    def __create_output_dir():
        """Create output directory if not exists."""
        root = os.path.abspath("..")

        directory = os.path.join(root, "output/job")
        if not os.path.exists(directory):
            os.makedirs(directory)

    def __driver_builder(self):
        """Init webdriver.

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

            .add_argument(f'user-agent={user_agent}')
            -> Add random UA

        Additionally, if use the visible window execution, you need to add the following operations

            .add_argument('--inprivate')
            -> Start by Private Browsing

            .add_argument("--start-maximized")
            -> Maximize the window

        Finally, inject script to change navigator = false.
        """
        user_agent = UserAgent().random

        options = webdriver.EdgeOptions()
        options.add_argument("headless")
        options.add_argument("--window-size=1920,1080")

        options.add_experimental_option(
            "excludeSwitches",
            ["enable-automation", "enable-logging"],
        )
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_experimental_option("useAutomationExtension", False)
        options.add_argument(f"user-agent={user_agent}")

        # options.add_argument('--inprivate')
        # options.add_argument("--start-maximized")

        web = webdriver.Edge(options=options)

        script = 'Object.defineProperty(navigator, "webdriver", {get: () => false,});'
        web.execute_script(script)
        return web

    def __slider_verify(self, web: webdriver):
        """Slider verification action.

        This requires the mouse to perform the following operations in following order

            1. put mouse on slider       ->   .move_to_element(slider)
            2. hold mouse on             ->   .click_and_hold()
            3. move to target position   ->   .move_by_offset(300, 0)

        Finally, perform action          ->   .perform()

        :Args:
         - web: Browser webdriver
        """
        slider = web.find_elements(By.XPATH, '//div[@class="nc_bg"]')

        if len(slider) <= 0:
            logger.warning("slider not found")
            return

        slider = slider[0]
        action_chains = (
            ActionChains(web)
            .move_to_element(slider)
            .click_and_hold()
            .move_by_offset(300 + random.randint(1, 20), 0)
        )

        action_chains.perform()

    def __save_to_csv(self, detail: dict, output: str):
        """Save dict data to csv.

        :Arg:
         - detail: Dictionary of a single data
         - output: Data output path
        """
        detail = [v for k, v in enumerate(detail.values())]
        df = pd.DataFrame([detail])
        df.to_csv(output, index=False, header=False, mode="a", encoding="utf-8")

    def __save_to_db(self, detail: dict, output: str):
        """Save dict data to sqlite.

        :Arg:
         - output: Data output path
        """
        connect = sqlite3.connect(output)
        cursor = connect.cursor()
        sqlTable = """CREATE TABLE IF NOT EXISTS `job51` (
                  `jobName` VARCHAR(255) NOT NULL,
                  `tags` VARCHAR(255) NULL,
                  `area` VARCHAR(50) NULL,
                  `salary` VARCHAR(255) NULL,
                  `workYear` VARCHAR(10) NULL,
                  `degree` VARCHAR(10) NULL,
                  `companyName` VARCHAR(255) NULL,
                  `companyType` VARCHAR(255) NULL,
                  `companySize` VARCHAR(10) NULL,
                  `logo` VARCHAR(255) NULL,
                  `issueDate` VARCHAR(50) NULL,
                  PRIMARY KEY (`jobName`,`area`,`companyName`,`issueDate`)
        );"""

        sql = """INSERT INTO `job51` VALUES(
            :jobName,
            :tags,
            :area,
            :salary,
            :workYear,
            :degree,
            :companyName,
            :companyType,
            :companySize,
            :logo,
            :issueDate
        );"""

        try:
            cursor.execute(sqlTable)
            cursor.execute(sql, detail)
            connect.commit()
        except Exception as e:
            logger.warning("SQL execution failure of SQLite: " + str(e))
        finally:
            cursor.close()
            connect.close()

    def save(self, items: json, type: str):
        """Iterate through the dictionary to get each item, save each data by specify type.

        Otherwise, the process will try to crawl work requirements and work position.
        If crawl failed, it is set empty and skip after three retries.

        Finally, add column header and remove duplicate rows

        :Args:
         - item: JSON data list
         - type: Data storage engine, support for csv, db and both
        """
        if items is None:
            return

        save_to = {
            "csv": lambda x: self.__save_to_csv(x, self.CSV_FILE_PATH),
            "db": lambda x: self.__save_to_db(x, self.SQLITE_FILE_PATH),
            "both": lambda x: (
                self.__save_to_csv(x, self.CSV_FILE_PATH),
                self.__save_to_db(x, self.SQLITE_FILE_PATH),
            ),
        }

        for key, item in enumerate(items):
            logger.info("processing in item" + str(key + 1))

            if "jobAreaLevelDetail" not in item:
                item["jobAreaLevelDetail"] = item["jobAreaString"]

            jobDetailDict = {
                "jobName": item["jobName"],
                "tags": ",".join(item["jobTags"]),
                "area": "".join(
                    re.findall(r"[\u4e00-\u9fa5]+", str(item["jobAreaLevelDetail"])),
                ),
                "salary": item["provideSalaryString"],
                "workYear": item["workYearString"],
                "degree": item["degreeString"],
                "companyName": item["fullCompanyName"],
                "companyType": item["companyTypeString"],
                "companySize": item["companySizeString"],
                "logo": item["companyLogo"],
                "issueDate": item["issueDateString"],
            }
            save = save_to[type]
            save(jobDetailDict)

        if type in ["csv", "both"]:
            label = [
                "jobName",
                "tags",
                "area",
                "salary",
                "workYear",
                "degree",
                "companyName",
                "companyType",
                "companySize",
                "logo",
                "issueDate",
            ]

            header = pd.read_csv(self.CSV_FILE_PATH, nrows=0).columns.tolist()
            names, set_header = None, False
            if not set(label).intersection(header):
                names = label
                set_header = True

            df = pd.read_csv(
                self.CSV_FILE_PATH,
                header=None,
                names=names,
                delimiter=",",
            )
            df.drop_duplicates(inplace=True)
            df.to_csv(
                self.CSV_FILE_PATH,
                index=False,
                header=set_header,
                encoding="utf-8",
            )

    def get_data_json(self):
        """Get job JSON data.

        The following is the execution order

            Driver building and start url
            Passing slider verification
            Getting HTML source
            Parsing HTML by BeautifulSoup, obtain the data through the first div
            Json Parsing

        Finally, return json data
        """
        extra = f"&timestamp={self.timestamp}&keyword={self.keyword}&pageNum={self.page}&pageSize={self.pageSize}&jobArea={self.area}"
        fake = self.fakeUrl.split("&")
        fake.remove(random.choice(fake))
        fake = "&".join(fake)

        url = self.baseUrl + extra + fake
        logger.info("Crawling page " + str(self.page))
        logger.info("Crawling " + url)

        web = self.__driver_builder()
        count = 3
        dataJson = None
        while count > 0:
            try:
                time.sleep(random.uniform(5, 10))
                web.get(url)

                time.sleep(random.uniform(1, 2))
                self.__slider_verify(web)
                time.sleep(random.uniform(1, 2))

                html = web.page_source
                soup = BeautifulSoup(html, "html.parser")
                data = soup.find("div").text

                dataJson = json.loads(data)

                if dataJson["status"] != "1":
                    logger.warning("Request failed, the request is unavailable")
                    dataJson = None
                    break

                dataJson = dataJson["resultbody"]["job"]["items"]
                break
            except Exception:
                count = count - 1
                logger.warning(
                    "data json sipder failed, waiting for try again, Remaining retry attempts: "
                    + str(count),
                )

        web.close()
        return dataJson


def start(args: dict, save_engine: str):
    """Spider starter.

    :Args:
     - param: Url param, type Dict{'keyword': str, 'page': int, 'pageSize': int, 'area': str}
     - save_engine: Data storage engine, support for csv, db and both
    """
    if save_engine not in ["csv", "db", "both"]:
        return logger.error("The data storage engine must be 'csv' , 'db' or 'both' ")

    spider = JobSipder51(
        keyword=args["keyword"],
        page=args["page"],
        pageSize=args["pageSize"],
        area=args["area"],
    )
    data_json = spider.get_data_json()
    spider.save(data_json, save_engine)
