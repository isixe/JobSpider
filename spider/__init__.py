# !/usr/bin/env python
# -*-coding:utf-8 -*-
# @Time    : 2023/11/26 20:22
# @Author  : isixe
# @Version : python3.10.6
# @Desc    : global spider logger

from log import handler_logger

logger = handler_logger.HandlerLogger(filename='spider.log')