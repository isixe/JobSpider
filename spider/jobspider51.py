"""This module is used to crawl 51job data."""

import json
import random
import re
import sqlite3
import time
import urllib.parse

from bs4 import BeautifulSoup
from fake_useragent import UserAgent
from selenium import webdriver
from selenium.common.exceptions import TimeoutException, WebDriverException
from selenium.webdriver import ActionChains
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC  # noqa: N812
from selenium.webdriver.support.ui import WebDriverWait

from spider import logger
from spider.config import (
    CHROMESERVICEPATH,
    FIREWALL_MESSAGE,
    HEIGHT_FACTOR,
    JOB_SQLITE_FILE_PATH,
    MAX_CLICKS,
    MAX_PAUSE,
    MAX_RETRIES,
    MAX_SLEEP,
    MIN_CLICKS,
    MIN_PAUSE,
    MIN_SLEEP,
    MOVE_DISTANCE,
    MOVE_VARIANCE,
    PROXY_GROUP,
    SLIDER_XPATH,
    STEPS,
    WAIT_TIME,
    WIDTH_FACTOR,
)


class JobSipder51:
    """This crawler is crawled based on the API."""

    def __init__(self, keyword: str, page: int, area: str) -> None:
        """Init the url param."""
        self.keyword = keyword
        self.page = page
        self.area = area
        self.timestamp = str(int(time.time()))
        self.baseUrl = "https://we.51job.com/api/job/search-pc?api_key=51job&searchType=2&pageCode=sou%7Csou%7Csoulb&sortType=0&function=&industry=&landmark=&metro=&requestId=&source=1&accountId="
        self.fakeUrl = "&jobArea2=&jobType=&salary=&workYear=&degree=&companyType="
        "&companySize=&issueDate="

    def _build_driver(self) -> webdriver:
        """Init webdriver.

        During the building process,
        it is necessary to set up an anti crawler detection strategy by Option.

            .add_argument('--no-sandbox')
            -> Disable sandbox mode

            .add_argument('headless')
            -> Set headless page, run silently

            .add_argument('--disable-dev-shm-usage')
            -> Disable shared memory

            .add_argument("--window-size=1920,1080")
            -> In headless status, browse without a window size,
                so if the size of the window is not specified,
            sliding verification may fail

            .add_experimental_option('excludeSwitches',['enable-automation','enable-logging'])
            -> Disable auto control and log feature of the browser

            .add_argument('--disable-blink-features=AutomationControlled')
            -> Disable auto control extension of the browser

            .add_argument(("useAutomationExtension", False))
            -> Disable auto control extension of the browser

            .add_argument(f'user-agent={user_agent}')
            -> Add random UA

        Additionally, if use the visible window execution,
        you need to add the following operations

            .add_argument('--inprivate')
            -> Start by Private Browsing

            .add_argument("--start-maximized")
            -> Maximize the window

        Finally, inject script to change navigator = false to avoid detection.
        """
        user_agent = UserAgent().random
        service = ChromeService(CHROMESERVICEPATH)

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
        options.add_experimental_option("useAutomationExtension", value=False)
        options.add_argument(f"user-agent={user_agent}")
        options.add_argument("--proxy-server=" + random.choice(PROXY_GROUP))

        web = webdriver.Chrome(service=service, options=options)
        web.execute_script(
            'Object.defineProperty(navigator, "webdriver", {get: () => false,});',
        )

        logger.info("Building webdriver done")

        return web

    def _slider_verify(self, web: webdriver) -> None:
        """Slider verification action."""
        try:
            slider = WebDriverWait(web, WAIT_TIME).until(
                EC.presence_of_element_located((By.XPATH, SLIDER_XPATH)),
            )
        except TimeoutException:
            logger.warning("Slider not found")
            return

        # Add random clicks to simulate human behavior
        for _ in range(random.randint(MIN_CLICKS, MAX_CLICKS)):
            # "/WIDTH_FACTOR" and "/HEIGHT_FACTOR" to avoid out of range
            x_offset = random.uniform(0, web.get_window_size()["width"] / WIDTH_FACTOR)
            y_offset = random.uniform(
                0,
                web.get_window_size()["height"] / HEIGHT_FACTOR,
            )
            ActionChains(web).pause(
                random.uniform(MIN_PAUSE, MAX_PAUSE),
            ).move_by_offset(x_offset, y_offset).click().perform()

        # Break down the movement into smaller steps
        action_chains = ActionChains(web).move_to_element(slider).click_and_hold()
        for _ in range(STEPS):
            action_chains.move_by_offset(
                MOVE_DISTANCE + random.uniform(0, MOVE_VARIANCE),
                0,
            )
            action_chains.pause(random.uniform(MIN_PAUSE, MAX_PAUSE))
        action_chains.release().perform()

    def _create_table(self, output: str) -> None:
        """Create table if not exists."""
        sql_table = """CREATE TABLE IF NOT EXISTS `job51` (
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

        try:
            with sqlite3.connect(output) as connect:
                cursor = connect.cursor()
                cursor.execute(sql_table)
                connect.commit()
        except sqlite3.Error as e:
            logger.warning("Failed to create table in SQLite: " + str(e))

    def _insert_to_db(self, detail: dict, output: str) -> None:
        """Insert data to SQLite."""
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
            with sqlite3.connect(output) as connect:
                cursor = connect.cursor()
                cursor.execute(sql, detail)
                connect.commit()
        except sqlite3.Error as e:
            logger.warning("SQL execution failure of SQLite: " + str(e))

    def save(self, items: json) -> None:
        """Iterate through the dictionary to get each item."""
        if items is None:
            return

        self._create_table(JOB_SQLITE_FILE_PATH)

        for _key, item in enumerate(items):
            if "jobAreaLevelDetail" not in item:
                item["jobAreaLevelDetail"] = item["jobAreaString"]

            job_detail_dict = {
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
            logger.info(f"Saving: {job_detail_dict}")
            self._insert_to_db(job_detail_dict, JOB_SQLITE_FILE_PATH)

    def _build_url(self) -> str:
        """Build the URL for the job search API."""
        base_url = urllib.parse.urlparse(self.baseUrl)

        extra_query_params = {
            "timestamp": self.timestamp,
            "keyword": self.keyword,
            "pageNum": self.page,
            "jobArea": self.area,
        }

        # fake to aviod detection
        fake_query_params = {
            "jobArea2": "",
            "jobType": "",
            "salary": "",
            "workYear": "",
            "degree": "",
            "companyType": "",
            "companySize": "",
            "issueDate": "",
        }
        # Randomly drop one or two parameters
        for _ in range(random.randint(1, 2)):
            if fake_query_params:
                random_key = random.choice(list(fake_query_params.keys()))
                del fake_query_params[random_key]

        base_query_params = urllib.parse.parse_qs(base_url.query)
        base_query_params.update(extra_query_params)
        base_query_params.update(fake_query_params)
        combined_url = urllib.parse.urlunparse(
            (
                base_url.scheme,
                base_url.netloc,
                base_url.path,
                base_url.params,
                urllib.parse.urlencode(base_query_params, doseq=True),
                base_url.fragment,
            ),
        )

        logger.info(f"Crawling {combined_url}")
        return combined_url

    def get_data_json(self) -> json:
        """Get the JSON data from the API."""
        url = self._build_url()
        web = self._build_driver()
        data_json = None

        try:
            for _ in range(MAX_RETRIES):
                try:
                    self._navigate_to_url(web, url)
                    self._bypass_slider_verification(web)
                    data_json = self._parse_html(web.page_source)
                    if data_json is not None:  # success to get data page
                        break
                except WebDriverException as e:
                    logger.warning(f"Failed to get data: {e}")
                    continue
            else:
                logger.warning("Failed to get data after all retries")
        finally:
            web.quit()  # to ensure the all browser is closed

        return data_json

    def _navigate_to_url(self, web: webdriver, url: str) -> None:
        """Navigate to the given URL."""
        time.sleep(random.uniform(MIN_SLEEP, MAX_SLEEP))
        web.get(url)
        self._varify_firewall(web)

    def _varify_firewall(self, web: webdriver) -> None:
        """Check if the request was blocked by a firewall."""
        soup = BeautifulSoup(web.page_source, "html.parser")
        if FIREWALL_MESSAGE in soup.text:
            msg = "Firewall detected"
            raise WebDriverException(msg)

    def _bypass_slider_verification(self, web: webdriver) -> None:
        """Pass the slider verification."""
        logger.info("Slider verification")
        time.sleep(random.uniform(MIN_SLEEP, MAX_SLEEP))
        self._slider_verify(web)

    def _parse_html(self, html: str) -> json:
        """Parse the HTML content and return the job items."""
        try:
            soup = BeautifulSoup(html, "html.parser")
            data = soup.find("body").text
            data_json = json.loads(data)
        except (AttributeError, json.JSONDecodeError) as e:
            logger.warning(f"Failed to parse HTML: {e}")
            return None

        if data_json.get("status") != "1":
            logger.warning("Request failed, the request is unavailable")
            return None

        # check if the key exists
        return data_json.get("resultbody", {}).get("job", {}).get("items")


def start(args: dict) -> None:
    """Spider starter."""
    spider = JobSipder51(
        keyword=args["keyword"],
        page=args["page"],
        area=args["area"],
    )
    data_json = spider.get_data_json()

    if data_json is None:
        logger.warning("No data to save")
        return

    logger.info(f"Saving {len(data_json)} items to {JOB_SQLITE_FILE_PATH}")
    spider.save(data_json)
