"""This is a file contains some function for selenium."""

import random
import time

from fake_useragent import UserAgent
from selenium import webdriver
from selenium.webdriver import ActionChains
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager

from spider import logger


# make the headless parameter required
def build_driver(*, headless: bool, proxy: str) -> webdriver:
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


def random_paruse() -> None:
    """Random pause."""
    return random.uniform(MIN_PAUSE, MAX_PAUSE)


def random_click(driver: webdriver, fraction: float = 1.0) -> None:
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
            x_offset, y_offset
        ).click().perform()


def random_scroll(driver: webdriver) -> None:
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
