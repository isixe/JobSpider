"""This file is used to store the configuration of the spider."""

import random
import sqlite3
import ssl
import time
from pathlib import Path
from typing import Any

import requests
import urllib3
from fake_useragent import UserAgent
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager

from spider import logger


class CustomHttpAdapter(requests.adapters.HTTPAdapter):
    """Transport adapter" that allows us to use custom ssl_context."""

    # ref: https://stackoverflow.com/a/73519818/16493978

    def __init__(self, ssl_context: Any = None, **kwargs: str | Any) -> None:  # noqa: ANN401
        """Init the ssl_context param."""
        self.ssl_context = ssl_context
        super().__init__(**kwargs)

    def init_poolmanager(
        self, connections: int, maxsize: int, *, block: bool = False
    ) -> None:
        """Create a urllib3.PoolManager for each proxy."""
        self.poolmanager = urllib3.poolmanager.PoolManager(
            num_pools=connections,
            maxsize=maxsize,
            block=block,
            ssl_context=self.ssl_context,
        )


def get_legacy_session() -> requests.Session:
    """Get legacy session."""
    ctx = ssl.create_default_context(ssl.Purpose.SERVER_AUTH)
    ctx.options |= 0x4  # OP_LEGACY_SERVER_CONNECT
    session = requests.session()
    session.mount("https://", CustomHttpAdapter(ctx))
    return session


def create_output_dir(tag: str) -> str:
    """Create output directory if not exists."""
    root = Path(__file__).resolve().parent.parent
    directory = root / f"output/{tag}"

    if not directory.exists():
        directory.mkdir(parents=True)
        logger.info(f"Directory {directory} created.")
    else:
        logger.info(f"Directory {directory} already exists.")
    return str(directory)


# make the headless parameter required
def build_driver(*, headless: bool) -> webdriver:
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
    user_agent = UserAgent().random
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

    if PROXY_GROUP:  # local not use proxy
        current_proxy = random.choice(PROXY_GROUP)
        options.add_argument("--proxy-server=" + current_proxy)
        logger.info(f"Using proxy {current_proxy}")

    driver = webdriver.Chrome(service=service, options=options)
    driver.execute_script(
        'Object.defineProperty(navigator, "webdriver", {get: () => false,});',
    )

    logger.info("Building webdriver done")

    return driver


def random_sleep() -> None:
    """Random sleep."""
    sleep_time = random.uniform(MIN_SLEEP, MAX_SLEEP)
    logger.info(f"Sleeping for {sleep_time} seconds")
    time.sleep(sleep_time)


def random_paruse() -> None:
    """Random pause."""
    return random.uniform(MIN_PAUSE, MAX_PAUSE)


def execute_sql_command(sql: str, path: Path, values: list | None = None) -> Any:  # noqa: ANN401
    """Execute a SQL command on the database."""
    try:
        with sqlite3.connect(path) as connect:
            cursor = connect.cursor()
            if values:
                cursor.execute(sql, values)
            else:
                cursor.execute(sql)

            # Fetch results for SELECT queries, otherwise return None for now
            if sql.strip().upper().startswith("SELECT"):
                return cursor.fetchall()

    except sqlite3.IntegrityError:
        logger.warning("SQL integrity error, not unique value")

    except sqlite3.Error as e:
        logger.warning(f"SQL execution failure of SQLite: {e!s}")
        raise


MAX_RETRIES = 3
MIN_SLEEP = 1
MAX_SLEEP = 3
CHROME_SERVICE_PATH = ChromeDriverManager().install()

# if in wsl/windows - code is 0, should use `get_legacy_session()`
# else use `requests.get()` - code is 1
PLAT_CODE = 0

if PLAT_CODE == 0:
    PROXY_GROUP = None
elif PLAT_CODE == 1:
    PROXY_GROUP = [  # set your proxy group
        "http://localhost:30001",
        "http://localhost:30002",
        "http://localhost:30003",
        "http://localhost:30004",
        "http://localhost:30005",
        "http://localhost:30006",
        "http://localhost:30007",
        "http://localhost:30008",
        "http://localhost:30009",
    ]

FIREWALL51_MESSAGE = "很抱歉，由于您访问的URL有可能对网站造成安全威胁，您的访问被阻断"  # noqa: RUF001

JOB51_SLIDER_XPATH = '//div[@class="nc_bg"]'
WAIT_TIME = 10
MIN_CLICKS = 1
MAX_CLICKS = 3
WIDTH_FACTOR = 3
HEIGHT_FACTOR = 3
MIN_PAUSE = 0.000001
MAX_PAUSE = 0.00005
STEPS = 30
MOVE_DISTANCE = 20
MOVE_VARIANCE = 0.01

# to avoid circular import
AREA51_SQLITE_FILE_PATH = Path(create_output_dir(tag="area")) / "51area.db"
JOB51_SQLITE_FILE_PATH = Path(create_output_dir(tag="job")) / "51job.db"

JOBOSS_SQLITE_FILE_PATH = Path(create_output_dir(tag="job")) / "bossjob.db"
AREABOSS_SQLITE_FILE_PATH = Path(create_output_dir(tag="area")) / "bossarea.db"

BOSS_COOKIES_FILE_PATH = Path(create_output_dir(tag="cookies")) / "BossCookies.json"

# main
MAX_51PAGE_NUM = 20
MAX_BOSSPAGE_NUM = 10
KEYWORD = "数据挖掘"
