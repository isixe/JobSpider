# !/usr/bin/env python
# -*-coding:utf-8 -*-
# @Time    : 2023/11/29 11:20
# @Author  : isixe
# @Version : python3.10.6
# @Desc    : customized log handler

import os
import logging
import sys
import colorlog
from logging.handlers import RotatingFileHandler


class HandlerLogger:
    """ Customized log handler,The main functions include console log highlighting
    and output formatting
    """

    def __init__(self, filename: str):
        self.logger = logging.getLogger()
        self.formatter = self.__init_formatter()
        self.color_formatter = self.__init_color_formatter()
        self.log_handler = self.__init_handler(filename=filename)
        self.console_handler = self.__init_console_handler()
        self.__set_log()
        self.__set_log_handler(self.log_handler)
        self.__set_console_handler(self.console_handler)

    def __set_log(self):
        """ Logging setting """

        self.logger.setLevel(logging.DEBUG)

    def __set_log_handler(self, log_handler: RotatingFileHandler):
        """ set log file logging handler

        :Arg:
         - log_handler: log file logging handler
        """

        log_handler.setLevel(logging.DEBUG)
        log_handler.setFormatter(self.formatter)
        self.logger.addHandler(log_handler)

    def __set_console_handler(self, console_handler: logging.StreamHandler):
        """ set console logging handler 
        
        :Arg:
         - console_handler: console logging handler
        """

        console_handler.setLevel(logging.DEBUG)
        console_handler.setFormatter(self.color_formatter)
        self.logger.addHandler(console_handler)

    @staticmethod
    def __init_handler(filename: str):
        """ init log file logging handler

        :Arg:
         - filename: log file prefix name
        """

        current_dir = os.path.dirname(__file__)
        abs_dir = os.path.join(current_dir, filename)
        handler = RotatingFileHandler(filename=abs_dir, maxBytes=512 * 1024, encoding='utf-8', backupCount=3)
        return handler

    @staticmethod
    def __init_console_handler():
        """ init console logging handler """

        console_handler = colorlog.StreamHandler(sys.stdout)
        return console_handler

    @staticmethod
    def __init_formatter():
        """ init log file formatter """

        LOG_FORMAT = '%(asctime)s [ %(levelname)s ]: %(message)s'
        DATE_FORMAT = '%m/%d/%Y %H:%M:%S %p'
        formater = logging.Formatter(LOG_FORMAT, DATE_FORMAT)
        return formater

    @staticmethod
    def __init_color_formatter():
        """ init console color formatter """

        LOG_FORMAT = ('%(log_color)s%(asctime)s %(log_color)s[ %(levelname)s%(reset)s%(log_color)s ]'
                      '%(reset)s%(log_color)s: %(message)s')
        DATE_FORMAT = '%m/%d/%Y %H:%M:%S %p'

        color_formatter = colorlog.ColoredFormatter(
            LOG_FORMAT,
            datefmt=DATE_FORMAT,
            log_colors={
                'DEBUG': 'cyan',
                'INFO': 'green',
                'WARNING': 'yellow',
                'ERROR': 'red',
                'CRITICAL': 'bold_red',
            }
        )
        return color_formatter

    def debug(self, message):
        """ Log msg with severity 'DEBUG'.

        :Arg
         - message: Log message
        """
        self.logger.debug(message)

    def info(self, message):
        """ Log msg with severity 'INFO'.

        :Arg
         - message: Log message
        """
        self.logger.info(message)

    def warning(self, message):
        """ Log msg with severity 'WARNING'.

        :Arg
         - message: log message
        """
        self.logger.warning(message)

    def error(self, message):
        """ Log msg with severity 'ERROR'.

        :Arg
         - message: log message
        """
        self.logger.error(message)

    def critical(self, message):
        """ Log msg with severity 'CRITICAL'.

        :Arg
         - message: log message
        """
        self.logger.critical(message)

    def close(self):
        """ logger close """

        self.logger.disabled = True
