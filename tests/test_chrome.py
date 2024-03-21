# Used for testing the Chrome browser with selenium

# If you not install webdriver,
# this script will install it automatically by webdriver_manager

# Notice that, ipv6 will cause some error, diable it if you have.
import requests

from log import handler_logger
from utility.proxy import Proxy
from utility.selenium_ext import build_driver


def test() -> None:
    logger = handler_logger.HandlerLogger(filename="test.log")
    proxy = Proxy(local=True).get()

    requests_response = requests.get(
        "https://www.baidu.com", proxies={"http": proxy}, timeout=10
    )
    logger.info("Response: %s", requests_response.text)

    driver = build_driver(headless=False, proxy=proxy)
    driver.get("https://www.baidu.com")
    logger.info("Response: %s", driver.page_source)

    driver.quit()
    logger.close()


if __name__ == "__main__":
    test()
