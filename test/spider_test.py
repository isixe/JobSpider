# !/usr/bin/env python
# -*-coding:utf-8 -*-
# @Time    : 2023/11/30 21:49
# @Author  : Exisi
# @Version : python3.10.6
# @Desc    : $END$

from spider import jobspider51

if __name__ == '__main__':
    param = {
        "keyword": "Python",
        "page": 1,
        "pageSize": 1000,
        "city": "000000"
    }
    jobspider51.start(args=param, save_engine='both')
