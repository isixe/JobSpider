"""This file is used to store the configuration of the spider."""
import os

from webdriver_manager.chrome import ChromeDriverManager

from spider.utility import create_output_dir

MAX_RETRIES = 3
MIN_SLEEP = 1
MAX_SLEEP = 3
CHROMESERVICEPATH = ChromeDriverManager().install()

PROXY_GROUP = [  # set your proxy group
    "http://localhost:30001",
    "http://localhost:30002",
    "http://localhost:30003",
]

# 51job
FIREWALL_MESSAGE = "很抱歉，由于您访问的URL有可能对网站造成安全威胁，您的访问被阻断"

AREA_DB_NAME = "51area.db"
SQLITE_FILE_PATH = os.path.join(create_output_dir(tag="area"), AREA_DB_NAME)

JOB_DB_NAME = "51job.db"
SQLITE_FILE_PATH = os.path.join(create_output_dir(tag="job"), JOB_DB_NAME)

SLIDER_XPATH = '//div[@class="nc_bg"]'
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
