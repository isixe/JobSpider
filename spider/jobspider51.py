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
from requests.exceptions import RequestException
from selenium import webdriver
from selenium.common.exceptions import TimeoutException, WebDriverException
from selenium.webdriver import ActionChains
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager

from spider import logger

MAX_RETRIES = 3
MIN_SLEEP = 1
MAX_SLEEP = 3


class JobSipder51:
    """This crawler is crawled based on the API."""

    def __init__(self, keyword: str, page: int, area: str):
        """Init the url param."""
        self.keyword = keyword
        self.page = page
        self.area = area
        self.timestamp = str(int(time.time()))
        self.baseUrl = "https://we.51job.com/api/job/search-pc?api_key=51job&searchType=2&pageCode=sou%7Csou%7Csoulb&sortType=0&function=&industry=&landmark=&metro=&requestId=&source=1&accountId="
        self.fakeUrl = "&jobArea2=&jobType=&salary=&workYear=&degree=&companyType=&companySize=&issueDate="
        self.current_dir = os.path.dirname(os.path.realpath(__file__))
        self.root = os.path.dirname(self.current_dir)
        self.CSV_FILE = "51job.csv"
        self.SQLITE_FILE = "51job.db"
        self.CSV_FILE_PATH = os.path.join(self.root, "output/job/" + self.CSV_FILE)
        self.SQLITE_FILE_PATH = os.path.join(
            self.root,
            "output/job/" + self.SQLITE_FILE,
        )
        self.__create_output_dir()

    def __create_output_dir(self):
        """Create output directory if not exists."""
        directory = os.path.join(self.root, "output/job")
        if not os.path.exists(directory):
            os.makedirs(directory)

    def __driver_builder(self):
        """Init webdriver.

        During the building process, it is necessary to set up an anti crawler detection strategy by Option.

            .add_argument('--no-sandbox')
            -> Disable sandbox mode

            .add_argument('headless')
            -> Set headless page, run silently

            .add_argument('--disable-dev-shm-usage')
            -> Disable shared memory

            .add_argument("--window-size=1920,1080")
            -> In headless status, browse without a window size, so if the size of the window is not specified,
            sliding verification may fail

            .add_experimental_option('excludeSwitches',['enable-automation','enable-logging'])
            -> Disable auto control and log feature of the browser

            .add_argument('--disable-blink-features=AutomationControlled')
            -> Disable auto control extension of the browser

            .add_argument(("useAutomationExtension", False))
            -> Disable auto control extension of the browser

            .add_argument(f'user-agent={user_agent}')
            -> Add random UA

        Additionally, if use the visible window execution, you need to add the following operations

            .add_argument('--inprivate')
            -> Start by Private Browsing

            .add_argument("--start-maximized")
            -> Maximize the window

        Finally, inject script to change navigator = false to avoid detection.
        """
        user_agent = UserAgent().random
        service = ChromeService(ChromeDriverManager().install())

        options = Options()
        options.add_argument("--no-sandbox")
        options.add_argument("--headless")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--window-size=1920,1080")
        options.add_experimental_option(
            "excludeSwitches",
            ["enable-automation", "enable-logging"],
        )
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_experimental_option("useAutomationExtension", False)
        options.add_argument(f"user-agent={user_agent}")

        web = webdriver.Chrome(service=service, options=options)
        web.execute_script(
            'Object.defineProperty(navigator, "webdriver", {get: () => false,});'
        )

        # cookie = web.get_cookies()
        # logger.info("Cookie: " + str(cookie))
        # In local wsl2, empty cookie works well

        logger.info("Building webdriver done")

        return web

    def __slider_verify(self, web: webdriver):
        """Slider verification action."""
        try:
            # Wait for the slider to be present in the DOM
            slider = WebDriverWait(web, 10).until(
                EC.presence_of_element_located((By.XPATH, '//div[@class="nc_bg"]'))
            )
        except TimeoutException:
            logger.warning("Slider not found")
            return

        slider = web.find_elements(By.XPATH, '//div[@class="nc_bg"]')[0]

        # Add random clicks to simulate human behavior
        for _ in range(random.randint(1, 3)):
            # "/3" to avoid out of range
            x = random.uniform(0, web.get_window_size()["width"] / 3)
            y = random.uniform(0, web.get_window_size()["height"] / 3)
            ActionChains(web).pause(random.uniform(0.000001, 0.00005)).move_by_offset(
                x, y
            ).click().perform()

        # Break down the movement into smaller steps
        action_chains = ActionChains(web).move_to_element(slider).click_and_hold()
        steps = 30  # Number of small steps
        for _ in range(steps):
            action_chains.move_by_offset(20 + random.uniform(0.005, 0.01), 0)
            action_chains.pause(
                random.uniform(0.000001, 0.00005)
            )  # Short delay between each step
        action_chains.release().perform()

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
        """Save dict data to sqlite."""
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
            logger.info("Saving: " + str(jobDetailDict))

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

    def build_url(self):
        """Build the URL for the job search API."""
        extra = f"&timestamp={self.timestamp}&keyword={self.keyword}&pageNum={self.page}&jobArea={self.area}"
        fake = self.fakeUrl.split("&")
        fake.remove(random.choice(fake))
        fake = "&".join(fake)
        url = self.baseUrl + extra + fake
        logger.info("Crawling " + url)
        return url

    def get_data_json(self):
        """Get the JSON data from the API."""
        url = self.build_url()
        web = self.__driver_builder()
        dataJson = None

        for _ in range(MAX_RETRIES):
            try:
                self.navigate_to_url(web, url)
                self.pass_slider_verification(web)
                dataJson = self.parse_html(web.page_source)
                if dataJson is not None:  # success to get data page
                    break
                else:  # no data page, jump to next
                    return
            except (WebDriverException, RequestException) as e:
                logger.warning(f"Failed due to {e}, retrying...")

        web.close()
        return dataJson

    def navigate_to_url(self, web, url):
        """Navigate to the given URL."""
        time.sleep(random.uniform(MIN_SLEEP, MAX_SLEEP))
        web.get(url)

    def pass_slider_verification(self, web):
        """Pass the slider verification."""
        logger.info("Slider verification")
        time.sleep(random.uniform(MIN_SLEEP, MAX_SLEEP))
        self.__slider_verify(web)

    def parse_html(self, html):
        """Parse the HTML content and return the job items."""
        try:
            soup = BeautifulSoup(html, "html.parser")
            data = soup.find("body").text
            dataJson = json.loads(data)
            if dataJson["status"] != "1":
                logger.warning("Request failed, the request is unavailable")
                return None
        except Exception as e:
            logger.warning(f"Failed to parse HTML: {e}")
            return None
        return dataJson["resultbody"]["job"]["items"]


def start(args: dict, save_engine: str):
    """Spider starter."""
    if save_engine not in ["csv", "db", "both"]:
        return logger.error("The data storage engine must be 'csv' , 'db' or 'both' ")

    spider = JobSipder51(
        keyword=args["keyword"],
        page=args["page"],
        area=args["area"],
    )
    data_json = spider.get_data_json()
    spider.save(data_json, save_engine)
