# !/usr/bin/env python
# -*-coding:utf-8 -*-
# @Time    : 2023/11/30 21:49
# @Author  : Exisi
# @Version : python3.10.6
# @Desc    : $END$

from spider import jobspider51

if __name__ == '__main__':
    for i in range(0, 10):
        param = {
            "keyword": "前端",
            "page": i + 1,
            "pageSize": 50,
            "city": "000000"
        }
        jobspider51.start(args=param, save_engine='db')
