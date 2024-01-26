# Using webdriver_manager to install the driver
from selenium import webdriver
from selenium.webdriver.edge.service import Service as EdgeService
from webdriver_manager.microsoft import EdgeChromiumDriverManager

msedgedriver_path = EdgeChromiumDriverManager().install()
print("Installed msedgedriver version:", msedgedriver_path)

service = EdgeService(executable_path=msedgedriver_path)
options = webdriver.EdgeOptions()

options.add_argument('--headless=new')
options.add_argument("--remote-debugging-port=0")
options.add_argument('--no-sandbox')

driver = webdriver.Edge(service=service, options=options)

print(driver.capabilities["browserVersion"])

driver.get("https://www.baidu.com")
title = driver.title
print(title)
