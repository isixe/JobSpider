"""This module contains constants used in the spider."""

WAIT_TIME = 10
MAX_RETRIES = 5

MAX_WAIT_TIME = 2
MIN_WAIT_TIME = 1

FIREWALL51_MESSAGE = "很抱歉，由于您访问的URL有可能对网站造成安全威胁，您的访问被阻断"  # noqa: RUF001
JOB51_SLIDER_XPATH = '//div[@class="nc_bg"]'

# slider in 51job
STEPS = 30
MOVE_DISTANCE = 20
MOVE_VARIANCE = 0.01

# main
MAX_51PAGE_NUM = 20
MAX_BOSSPAGE_NUM = 10
KEYWORD = "数据挖掘"
MAX_ASY_NUM = 10
