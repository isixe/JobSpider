"""This module is used to crawl 51job data."""

import json
import random
import re
import time
import urllib.parse

from bs4 import BeautifulSoup
from fake_useragent import UserAgent  # type: ignore[import-untyped]
from selenium import webdriver
from selenium.common.exceptions import TimeoutException, WebDriverException
from selenium.webdriver import ActionChains
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions as EC  # noqa: N812
from selenium.webdriver.support.wait import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager

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
from utility.sql import execute_sql_command


class JobSipder51:
    """This crawler is crawled based on the API."""

    driver: webdriver.Chrome
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
                int(MOVE_DISTANCE + random.uniform(0, MOVE_VARIANCE)),
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

    def _insert_to_db(self, detail: list[tuple[str]]) -> None:
        """Insert data to SQLite."""
        sql = """INSERT OR IGNORE INTO `job51` (
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
        ) VALUES (:jobName, :tags, :area, :salary, :workYear,
                  :degree, :companyName, :companyType, :companySize, :logo, :issueDate);
        """

        execute_sql_command(sql, JOB51_SQLITE_FILE_PATH, detail)

    def save(self, items: dict) -> None:
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
            "https://we.51job.com/api/job/search-pc"
            "?api_key=51job&searchType=2&pageCode=sou%7Csou%7Csoulb"
            "&sortType=0&function=&industry=&landmark=&metro=&requestId=&source=1&accountId="
        )

        extra_query_params = {
            "timestamp": timestamp,
            "keyword": keyword,
            "pageNum": str(page),
            "jobArea": area,
        }

        # fake to avoid detection
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
        base_query_params.update((k, [v]) for k, v in extra_query_params.items())
        base_query_params.update((k, [v]) for k, v in fake_query_params.items())
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

    def get_data_json(self) -> dict | None:
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

    def _parse_html(self) -> dict | None:
        """Parse the HTML content and return the job items."""
        html = self.driver.page_source
        try:
            soup = BeautifulSoup(html, "html.parser")
            data_ele = soup.find("body")
            if data_ele is None:
                logger.warning("Failed to find the data element")
                return None
            data = data_ele.text
            data_json = json.loads(data)
        except (AttributeError, json.JSONDecodeError) as e:
            logger.warning(f"Failed to parse HTML: {e}")
            return None

        if data_json.get("status") != "1":
            logger.warning("Request failed, the request is unavailable")
            return None

        # check if the key exists
        return data_json.get("resultbody", {}).get("job", {}).get("items")


def start(args: dict[str, str]) -> None:
    """Spider starter."""
    spider = JobSipder51(
        keyword=args["keyword"],
        page=int(args["page"]),
        area=args["area"],
    )
    data_json = spider.get_data_json()

    if data_json is None:
        logger.warning("No data to save")
        return

    logger.info(f"Saving {len(data_json)} items to {JOB51_SQLITE_FILE_PATH}")
    spider.save(data_json)


def build_driver(*, headless: bool, proxy: str) -> webdriver.Chrome:
    """Init webdriver, don't forget to close it.

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
    user_agent = UserAgent(os=["windows", "macos"]).random
    service = ChromeService(CHROME_SERVICE_PATH)

    options = Options()
    options.add_argument("--no-sandbox")

    if headless:
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

    options.add_argument(f"--proxy-server={proxy}")

    options.add_argument("Accept-Language: zh-CN,zh;q=0.9")

    driver = webdriver.Chrome(service=service, options=options)
    driver.execute_script(
        'Object.defineProperty(navigator, "webdriver", {get: () => undefined});',
    )

    logger.info("Building webdriver done")

    return driver


def random_sleep() -> None:
    """Random sleep."""
    sleep_time = random.uniform(MIN_SLEEP, MAX_SLEEP)
    logger.info(f"Sleeping for {sleep_time} seconds")
    time.sleep(sleep_time)


def random_paruse() -> float:
    """Random pause."""
    return random.uniform(MIN_PAUSE, MAX_PAUSE)


def random_click(driver: webdriver.Chrome, fraction: float = 1.0) -> None:
    """Add random clicks to simulate human behavior."""
    for _ in range(random.randint(MIN_CLICKS, MAX_CLICKS)):
        # "/WIDTH_FACTOR" and "/HEIGHT_FACTOR" to avoid out of range
        x_offset = random.uniform(
            0, driver.get_window_size()["width"] / fraction / WIDTH_FACTOR
        )
        y_offset = random.uniform(
            0,
            driver.get_window_size()["height"] / fraction / HEIGHT_FACTOR,
        )
        ActionChains(driver).pause(random_paruse()).move_by_offset(
            int(x_offset), int(y_offset)
        ).click().perform()


def random_scroll(driver: webdriver.Chrome) -> None:
    """Scrolls down the page by a random amount."""
    random_paruse()
    scroll_height = driver.execute_script("return document.body.scrollHeight")
    scroll_target = random.randint(0, scroll_height)
    driver.execute_script(f"window.scrollTo(0, {scroll_target});")


MIN_SLEEP = 1
MAX_SLEEP = 1.5
CHROME_SERVICE_PATH = ChromeDriverManager().install()

MIN_CLICKS = 1
MAX_CLICKS = 3
WIDTH_FACTOR = 3
HEIGHT_FACTOR = 3
MIN_PAUSE = 0.000001
MAX_PAUSE = 0.00005
