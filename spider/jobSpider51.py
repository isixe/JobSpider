# !/usr/bin/env python
# -*-coding:utf-8 -*-
# @Time    : 2023/10/31 10:36
# @Author  : isixe
# @Version : python3.10.6
# @Desc    : job data spider

import os
import random
import re
import json
import time
import pandas as pd
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver import ActionChains
from selenium.webdriver.common.by import By
from log import handlerLogger

logger = handlerLogger.HandlerLogger(filename='spider.log')


class JobSipder51(object):
    """ This crawler is crawled based on the API"""

    def __init__(self, param: dict):
        """ Init the url param

        :Args:
         - param: Url param dict -> key{'keyword','page','pageSize','city'}
        """
        self.keyword = param['keyword']
        self.page = param['page']
        self.pageSize = param['pageSize']
        self.city = param['city']
        self.baseUrl = ('https://we.51job.com/api/job/search-pc?api_key=51job&searchType=2&function=&industry='
                        '&jobArea2=&landmark=&metro=&salary=&workYear=&degree=&companyType=&companySize=&jobType='
                        '&issueDate=&sortType=0&pageNum=1&requestId=&source=1&accountId=&pageCode=sou%7Csou%7Csoulb')
        self.CSV_FILE = '51job.csv'
        self.create_output_dir()

    @staticmethod
    def create_output_dir():
        """ Create output directory if not exists """
        root = os.path.abspath('..')

        directory = os.path.join(root, "output")
        if not os.path.exists(directory):
            os.makedirs(directory)

    def get_data_json(self):
        """ Get job JSON data

        The following is the execution order

            Driver building and start url
            Passing slider verification
            Getting HTML source
            Parsing HTML by BeautifulSoup, obtain the data through the first div
            Json Parsing

        Finally, return json data
        """

        extra = f"&keyword={self.keyword}&pageSize={self.pageSize}&jobArea={self.city}"
        url = self.baseUrl + extra
        web = self.driver_builder()
        web.get(url)

        time.sleep(2)
        self.slider_verify(web)
        time.sleep(3)

        html = web.page_source
        soup = BeautifulSoup(html, "html.parser")
        data = soup.find('div').text

        dataJson = json.loads(data)
        dataJson = dataJson['resultbody']['job']['items']
        web.close()
        return dataJson

    def driver_builder(self):
        """ Init webdriver

        During the building process, it is necessary to set up an anti crawler detection strategy by Option.

            .add_argument('headless')
            -> Set headless page, run silently

            .add_argument("--window-size=1920,1080")
            -> In headless status, browse without a window size, so if the size of the window is not specified,
            sliding verification may fail

            .add_experimental_option('excludeSwitches',['enable-automation','enable-logging'])
            -> Disable auto control and log feature of the browser

            .add_argument('--disable-blink-features=AutomationControlled')
            -> Set navigator.webdriver=false

            .add_argument('--disable-blink-features=AutomationControlled')
            -> Disable auto control extension of the browser

        Additionally, if use the visible window execution, you need to add the following operations

            .add_argument('--inprivate')
            -> Start by Private Browsing

            .add_argument("--start-maximized")
            -> Maximize the window

        Finally, inject script to change navigator = false.
        """

        options = webdriver.EdgeOptions()
        options.add_argument('headless')
        options.add_argument("--window-size=1920,1080")

        options.add_experimental_option('excludeSwitches', ['enable-automation', 'enable-logging'])
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_experimental_option('useAutomationExtension', False)
        # options.add_argument('--inprivate')
        # options.add_argument("--start-maximized")

        web = webdriver.Edge(options=options)

        script = 'Object.defineProperty(navigator, "webdriver", {get: () => false,});'
        web.execute_script(script)
        return web

    def slider_verify(self, web: webdriver):
        """ Slider verification action

        This requires the mouse to perform the following operations in following order

            1. put mouse on slider       ->   .move_to_element(slider)
            2. hold mouse on             ->   .click_and_hold()
            3. move to target position   ->   .move_by_offset(300, 0)

        Finally, perform action          ->   .perform()
        """
        slider = web.find_element(By.XPATH, '//div[@class="nc_bg"]')

        action_chains = (ActionChains(web)
                         .move_to_element(slider)
                         .click_and_hold()
                         .move_by_offset(300 + random.randint(1, 20), 0))

        action_chains.perform()

    def save(self, items: json, type: str):
        """ Iterate through the dictionary to get each item, save each data by specify type.
        Finally, add column header
        """
        root = os.path.abspath('..')
        CSV_FILE_PATH = os.path.join(root, "output/" + self.CSV_FILE)

        save_to = {
            'csv': lambda x: self.save_to_csv(x, CSV_FILE_PATH),
            'db': lambda x: self.save_to_db(x)
        }

        for key, item in enumerate(items):
            logger.info('processing in item' + str(key + 1))

            jobDetailDict = {
                'jobName': item['jobName'],
                'tags': ",".join(item['jobTags']),
                'city': ''.join(re.findall(r'[\u4e00-\u9fa5]+', str(item['jobAreaLevelDetail']))),
                'salary': item['provideSalaryString'],
                'workYear': item['workYearString'],
                'degree': item['degreeString'],
                'jobRequire': item['jobHref'],
                'companyName': item['fullCompanyName'],
                'companyType': item['companyTypeString'],
                'companySize': item['companySizeString'],
                'logo': item['smallHrLogoUrl'],
                'issueDate': item['issueDateString']
            }
            save = save_to[type]
            save(jobDetailDict)

        if type == 'csv':
            label = (['职位名称', '标签', '城市', '薪资', '工作年限', '学位要求',
                      '工作要求', '公司名称', '公司类型', '人数', 'Logo', '发布时间'])

            header = pd.read_csv(CSV_FILE_PATH, nrows=0)
            header = header.columns.tolist()

            if not set(label).intersection(header):
                df = pd.read_csv(CSV_FILE_PATH, header=None, names=label)
                df.drop_duplicates(inplace=True)
                df.to_csv(CSV_FILE_PATH, index=False)

    def save_to_csv(self, detail: dict, output: str):
        """ Save json data to csv """

        detail = [v for k, v in enumerate(detail.values())]
        df = pd.DataFrame([detail])
        df.to_csv(output, index=False, header=False, mode='a')




if __name__ == '__main__':
    param = {
        "keyword": "android",
        "page": 10,
        "pageSize": 50,
        "city": "000000"
    }

    spider = JobSipder51(param)
    json = spider.get_data_json()
    spider.save(json, 'csv')
