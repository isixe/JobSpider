# !/usr/bin/env python
# -*-coding:utf-8 -*-
# @Time    : 2023/11/30 21:49
# @Author  : Exisi
# @Version : python3.10.6
# @Desc    : base spider test
import sqlite3
import pandas as pd
from spider.area import areaspider51
from spider import jobspider51, logger


def area():
    areaspider51.start(save_engine='both')


def part_spider():
    param = {
        "keyword": "Python",
        "page": 1,
        "pageSize": 1000,
        "area": "000000"
    }
    jobspider51.start(args=param, save_engine='both')


def full_spider(save_engine: str):
    save_to = {
        'csv': lambda x: full_spider_csv(x),
        'db': lambda x: full_spider_db(x),
        'both': lambda x: full_spider_csv(x)
    }
    save = save_to[save_engine]
    save(save_engine)


def full_spider_csv(type: str):
    df = pd.read_csv('../output/area/51area.csv', header=None, names=None, skiprows=1, delimiter=',')

    for area in df[0]:
        param = {
            "keyword": "Python",
            "page": 1,
            "pageSize": 1000,
            "area": area
        }
        jobspider51.start(args=param, save_engine=type)


def full_spider_db(type: str):
    results = None
    connect = sqlite3.connect("../output/area/51area.db")
    cursor = connect.cursor()
    sql = '''SELECT `code` FROM `area51`;'''
    try:
        cursor.execute(sql)
        results = cursor.fetchall()
        connect.commit()
    except Exception as e:
        logger.warning("SQL execution failure of SQLite: " + str(e))
    finally:
        cursor.close()
        connect.close()

    for area in results:
        param = {
            "keyword": "Python",
            "page": 1,
            "pageSize": 1000,
            "area": area[0]
        }
        jobspider51.start(args=param, save_engine=type)


if __name__ == '__main__':
    area()
    full_spider(save_engine='both')
