"""This module is used to crawl 51job data."""

import json
import random
import re
import time
import urllib.parse

from bs4 import BeautifulSoup
from selenium.common.exceptions import TimeoutException, WebDriverException
from selenium.webdriver import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions as EC  # noqa: N812
from selenium.webdriver.support.ui import WebDriverWait

from spider import logger
from utility.constant import (
    FIREWALL51_MESSAGE,
    JOB51_SLIDER_XPATH,
    MAX_RETRIES,
    MOVE_DISTANCE,
    MOVE_VARIANCE,
    STEPS,
    WAIT_TIME,
)
from utility.path import JOB51_SQLITE_FILE_PATH
from utility.proxy import Proxy
from utility.selenium_ext import (
    build_driver,
    random_click,
    random_paruse,
    random_sleep,
)
from utility.sql import execute_sql_command


class JobSipder51:
    """This crawler is crawled based on the API."""

    driver: WebDriver
    url: str

    def __init__(self, keyword: str, page: int, area: str) -> None:
        """Init the url param."""
        self.url = self._build_url(keyword, page, area)
        self.driver = build_driver(headless=False, proxy=Proxy(local=True).get())

    def _slider_verify(self) -> None:
        """Slider verification action."""
        try:
            slider = WebDriverWait(self.driver, WAIT_TIME).until(
                EC.presence_of_element_located((By.XPATH, JOB51_SLIDER_XPATH)),
            )
        except TimeoutException:
            logger.warning("Slider not found")
            return

        # Add random clicks to simulate human behavior
        random_click(self.driver)
        # Break down the movement into smaller steps
        self._small_move(slider)

    def _small_move(self, slider: WebElement) -> None:
        """Break down the movement into smaller steps."""
        action_chains = (
            ActionChains(self.driver).move_to_element(slider).click_and_hold()
        )
        for _ in range(STEPS):
            action_chains.move_by_offset(
                MOVE_DISTANCE + random.uniform(0, MOVE_VARIANCE),
                0,
            )
            action_chains.pause(random_paruse())
        action_chains.release().perform()

    def _create_table(self) -> None:
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

        execute_sql_command(sql_table, JOB51_SQLITE_FILE_PATH)

    def _insert_to_db(self, detail: dict) -> None:
        """Insert data to SQLite."""
        sql = """INSERT INTO `job51` (
            `jobName`,
            `tags`,
            `area`,
            `salary`,
            `workYear`,
            `degree`,
            `companyName`,
            `companyType`,
            `companySize`,
            `logo`,
            `issueDate`
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
        """

        execute_sql_command(sql, JOB51_SQLITE_FILE_PATH, detail)

    def save(self, items: json) -> None:
        """Iterate through the dictionary to get each item."""
        if not items:
            return

        self._create_table()

        jobs = [
            {
                "jobName": item.get("jobName"),
                "tags": ",".join(item.get("jobTags", [])),
                "area": "".join(
                    re.findall(
                        r"[\u4e00-\u9fa5]+",
                        str(item.get("jobAreaLevelDetail", item.get("jobAreaString"))),
                    )
                ),
                "salary": item.get("provideSalaryString"),
                "workYear": item.get("workYearString"),
                "degree": item.get("degreeString"),
                "companyName": item.get("fullCompanyName"),
                "companyType": item.get("companyTypeString"),
                "companySize": item.get("companySizeString"),
                "logo": item.get("companyLogo"),
                "issueDate": item.get("issueDateString"),
            }
            for item in items
        ]

        self._insert_to_db([tuple(job.values()) for job in jobs])

    def _build_url(self, keyword: str, page: int, area: str) -> str:
        """Build the URL for the job search API."""
        timestamp = str(int(time.time()))
        base_url = urllib.parse.urlparse(
            "https://we.51job.com/api/job/search-pc?api_key=51job&searchType=2&pageCode=sou%7Csou%7Csoulb&sortType=0&function=&industry=&landmark=&metro=&requestId=&source=1&accountId="
        )

        extra_query_params = {
            "timestamp": timestamp,
            "keyword": keyword,
            "pageNum": page,
            "jobArea": area,
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
        data_json = None

        try:
            for _ in range(MAX_RETRIES):
                try:
                    self._navigate_to_url()
                    self._bypass_slider_verification()
                    data_json = self._parse_html()
                    if data_json is not None:  # success to get data page
                        break
                except WebDriverException as e:
                    logger.warning(f"Failed to get data: {e}")
                    continue
            else:
                logger.warning("Failed to get data after all retries")
        finally:
            self.driver.quit()  # to ensure the all browser is closed

        return data_json

    def _navigate_to_url(self) -> None:
        """Navigate to the given URL."""
        random_sleep()
        self.driver.get(self.url)
        self._varify_firewall()

    def _varify_firewall(self) -> None:
        """Check if the request was blocked by a firewall."""
        soup = BeautifulSoup(self.driver.page_source, "html.parser")
        if FIREWALL51_MESSAGE in soup.text:
            msg = "Firewall detected"
            raise WebDriverException(msg)

    def _bypass_slider_verification(self) -> None:
        """Pass the slider verification."""
        logger.info("Slider verification")
        random_sleep()
        self._slider_verify()

    def _parse_html(self) -> json:
        """Parse the HTML content and return the job items."""
        html = self.driver.page_source
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

    logger.info(f"Saving {len(data_json)} items to {JOB51_SQLITE_FILE_PATH}")
    spider.save(data_json)
