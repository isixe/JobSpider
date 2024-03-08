"""This is a spider for Boss."""

import json
import time
import urllib.parse
from pathlib import Path

from bs4 import BeautifulSoup
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.support import expected_conditions as EC  # noqa: N812
from selenium.webdriver.support.ui import WebDriverWait

from spider import logger
from spider.utility import (
    BOSS_COOKIES_FILE_PATH,
    JOBOSS_SQLITE_FILE_PATH,
    MAX_RETRIES,
    build_driver,
    execute_sql_command,
    random_sleep,
)

# Boss limit 10 pages for each query
# if add more query keywords, result will be different


class LoginManager:
    """Login manager for Boss."""

    def __init__(self, driver: WebDriver) -> None:
        """Init."""
        self.driver = driver
        self.cookies = None
        self.url = "https://www.zhipin.com/web/user/?ka=header-login"

    def login(self, timeout: int = 60) -> None:
        """Login and get cookies within timeout."""
        logger.info("Start to login")
        if self._cache_login():
            logger.info("Login success using cache cookies")
            return

        self._login_manually(timeout)

    def _login_force(self) -> None:
        """Force login."""
        self._clear_cookies()
        self._login_manually()

    def _login_manually(self, timeout: int = 60) -> None:
        """Login manually."""
        logger.info("Please login manually")
        self.driver.get(self.url)
        self.cookies = self.driver.get_cookies()

        # Wait for login
        start_time = time.time()
        while time.time() - start_time < timeout:
            time.sleep(0.1)
            self.cookies = self.driver.get_cookies()
            if self._valid_cookie():
                with Path(BOSS_COOKIES_FILE_PATH).open("w") as f:
                    json.dump(self.cookies, f)
                logger.info("Login success")
                break
        else:
            logger.error("Login timed out")

    def _cache_login(self) -> bool:
        """Login and get cookies."""
        self._read_cookies()
        if self._valid_cookie():
            self._update_cookies()
            return True
        return False

    def _valid_cookie(self) -> bool:
        """Check if the cookies are valid."""
        if self.cookies is None:
            return False
        cookie_names = {cookie["name"] for cookie in self.cookies}
        required_cookies = {"geek_zp_token", "zp_at"}
        return required_cookies.issubset(cookie_names)

    def _clear_cookies(self) -> None:
        """Clear cookies."""
        self.driver.delete_all_cookies()
        self.cookies = None
        if Path(BOSS_COOKIES_FILE_PATH).exists():
            Path.unlink(BOSS_COOKIES_FILE_PATH)

    def _read_cookies(self) -> None:
        """Read cookies from file."""
        if Path(BOSS_COOKIES_FILE_PATH).exists():
            with Path(BOSS_COOKIES_FILE_PATH).open("r") as f:
                self.cookies = json.load(f)

    def _update_cookies(self) -> None:
        """Update cookies."""
        self.driver.get(self.url)
        for cookie in self.cookies:
            self.driver.add_cookie(cookie)
        logger.info("Update cookies")


class JobSpiderBoss:
    """This is a spider for Boss."""

    driver: WebDriver

    def __init__(self, keyword: str, city: str) -> None:
        """Init."""
        self.keyword = keyword
        self.city = city
        self.page = 1
        self.max_page = 10

        self.driver = self._build_driver()

    def start(self) -> None:
        """Crawl the job list."""
        self._create_table()
        while self.page <= self.max_page:
            self.url = self._build_url(self.keyword, self.city)
            self._crwal_sigle_page()
            self.page += 1
        self.driver.quit()

    def _build_driver(self) -> None:
        """Build the driver."""
        self.driver = build_driver(headless=False)
        # Not login, using other way to avoid the anti-crawler detection
        # LoginManager(self.driver).login() # noqa: ERA001

    def _build_url(self, keyword: str, city: str) -> str:
        """Build the URL for the job search."""
        base_url = "https://www.zhipin.com/web/geek/job"
        query_params = urllib.parse.urlencode(
            {"query": keyword, "city": city, "page": self.page}
        )
        url = f"{base_url}?{query_params}"
        logger.info(f"Crawling {self.city} of page-{self.page}, {url}")
        return url

    def _crwal_sigle_page(self) -> str:
        """Get the HTML from the URL."""
        random_sleep()
        try:
            for _ in range(MAX_RETRIES):
                try:
                    self.driver.get(self.url)

                    job_list = WebDriverWait(self.driver, 60).until(
                        EC.presence_of_element_located((By.CLASS_NAME, "job-list-box"))
                    )

                    max_page = int(
                        self.driver.find_elements(By.CLASS_NAME, "options-pages")[
                            0
                        ].text[-1]
                    )
                    if max_page == 0:
                        self.max_page = 10
                    else:
                        self.max_page = int(max_page)
                    break

                except TimeoutException:
                    logger.error("TimeoutException of getting job list, retrying")
                    self.driver = (
                        self._build_driver()
                    )  # rebuild driver, refreshing proxy to retry
                    continue
        finally:
            self.driver.quit()

        self._parse_job_list(job_list.get_attribute("innerHTML"))

    def _parse_job_list(self, job_list: str) -> None:
        """Parse the HTML and get the JSON data."""
        soup = BeautifulSoup(job_list, "html.parser")
        job_card = soup.find_all("li", class_="job-card-wrapper")
        for job in job_card:
            self._insert_to_db(self._parse_job(job))

    def _parse_job(self, job: BeautifulSoup) -> dict:
        job_name = job.find("span", class_="job-name").text
        job_area = job.find("span", class_="job-area").text
        job_salary = job.find("span", class_="salary").text
        edu_exp = ",".join(
            [
                li.text
                for li in job.find("div", class_="job-info clearfix").find_all("li")
            ]
        )

        _company_info = job.find("div", class_="company-info")
        company_name = _company_info.find("h3", class_="company-name").text
        company_tag = ",".join(
            [
                li.text
                for li in _company_info.find("ul", class_="company-tag-list").find_all(
                    "li"
                )
            ]
        )

        _cardbottom = job.find("div", class_="job-card-footer clearfix")
        skill_tags = ",".join(
            [li.text for li in _cardbottom.find("ul", class_="tag-list").find_all("li")]
        )
        job_other_tags = ",".join(
            _cardbottom.find("div", class_="info-desc").text.split(
                "，"  # noqa: RUF001
            )
        )
        return {
            "job_name": job_name,
            "job_area": job_area,
            "job_salary": job_salary,
            "edu_exp": edu_exp,
            "company_name": company_name,
            "company_tag": company_tag,
            "skill_tags": skill_tags,
            "job_other_tags": job_other_tags,
        }

    def _insert_to_db(self, job_data: dict) -> None:
        """Insert the data into the database."""
        sql = """
        INSERT INTO `joboss` (
            `job_name`,
            `area`,
            `salary`,
            `edu_exp`,
            `company_name`,
            `company_tag`,
            `skill_tags`,
            `job_other_tags`
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?);
        """

        execute_sql_command(sql, JOBOSS_SQLITE_FILE_PATH, list(job_data.values()))

    def _create_table(self) -> None:
        """Create the table in the database."""
        sql_table = """
        CREATE TABLE IF NOT EXISTS `joboss` (
            `job_name` TEXT NULL,
            `area` TEXT NULL,
            `salary` TEXT NULL,
            `edu_exp` TEXT NULL,
            `company_name` TEXT NULL,
            `company_tag` TEXT NULL,
            `skill_tags` TEXT NULL,
            `job_other_tags` TEXT NULL,
            PRIMARY KEY (`job_name`, `company_name`, `area`, `salary`, `skill_tags`)
        );
        """

        execute_sql_command(sql_table, JOBOSS_SQLITE_FILE_PATH)


def start(keyword: str, area_code: str) -> None:
    """Start the spider."""
    JobSpiderBoss(keyword, area_code).start()
    logger.close()
