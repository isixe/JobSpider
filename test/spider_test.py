# !/usr/bin/env python
# -*-coding:utf-8 -*-
# @Time    : 2023/11/30 21:49
# @Author  : Exisi
# @Version : python3.10.6
# @Desc    : base spider test

from spider import jobspider51
from spider.city import areaspider51


def area():
    areaspider51.start(save_engine='both')


def job():
    param = {
        "keyword": "Python",
        "page": 1,
        "pageSize": 1000,
        "area": "000000"
    }
    jobspider51.start(args=param, save_engine='both')


if __name__ == '__main__':
    area()
    job()
