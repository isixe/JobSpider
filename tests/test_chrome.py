# Used for testing the Chrome browser with selenium
# If you not install webdriver,
# this script will install it automatically by webdriver_manager

# Notice that, ipv6 will cause some error, diable it if you have.
from fake_useragent import UserAgent
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager

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
options.add_argument(f"user-agent={UserAgent().random}")
driver = webdriver.Chrome(
    service=ChromeService(ChromeDriverManager().install()),
    options=options,
)

script = 'Object.defineProperty(navigator, "webdriver", {get: () => false,});'
driver.execute_script(script)

driver.get("https://www.baidu.com")
driver.quit()  # quit to close all open windows
