"""Customized log handler."""

import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path

import colorlog


class HandlerLogger:
    """Customized log handler.

    The main functions include console log highlightingand output formatting.
    """

    def __init__(self, filename: str) -> None:
        """Initialize the HandlerLogger class.

        :param filename: The log file prefix name.
        """
        self.logger = logging.getLogger()
        self.formatter = self.__init_formatter()
        self.color_formatter = self.__init_color_formatter()
        self.log_handler = self.__init_handler(filename=filename)
        self.console_handler = self.__init_console_handler()
        self.__set_log()
        self.__set_log_handler(self.log_handler)
        self.__set_console_handler(self.console_handler)

    def __set_log(self) -> None:
        """Set logging configuration."""
        self.logger.setLevel(logging.DEBUG)

    def __set_log_handler(self, log_handler: RotatingFileHandler) -> None:
        """Set log file logging handler."""
        log_handler.setLevel(logging.INFO)
        log_handler.setFormatter(self.formatter)
        self.logger.addHandler(log_handler)

    def __set_console_handler(self, console_handler: logging.StreamHandler) -> None:
        """Set console logging handler.

        :Arg:
         - console_handler: console logging handler
        """
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(self.color_formatter)
        self.logger.addHandler(console_handler)

    @staticmethod
    def __init_handler(filename: str) -> RotatingFileHandler:
        """Init log file logging handler."""
        current_dir = Path(__file__).parent
        abs_dir = current_dir / filename
        return RotatingFileHandler(
            filename=abs_dir,
            maxBytes=1024 * 1024,
            encoding="utf-8",
            backupCount=3,
        )

    @staticmethod
    def __init_console_handler() -> logging.StreamHandler:
        """Init console logging handler."""
        return colorlog.StreamHandler(sys.stdout)

    @staticmethod
    def __init_formatter() -> logging.Formatter:
        """Init log file formatter."""
        log_format = "%(asctime)s [ %(levelname)s ]: %(message)s"
        date_format = "%m/%d/%Y %H:%M:%S %p"
        return logging.Formatter(log_format, date_format)

    @staticmethod
    def __init_color_formatter() -> colorlog.ColoredFormatter:
        """Init console color formatter."""
        log_format = (
            "%(log_color)s%(asctime)s %(log_color)s[ %(levelname)s%(reset)s"
            "%(log_color)s ]%(reset)s%(log_color)s: %(message)s"
        )
        date_format = "%m/%d/%Y %H:%M:%S %p"

        return colorlog.ColoredFormatter(
            log_format,
            datefmt=date_format,
            log_colors={
                "DEBUG": "cyan",
                "INFO": "green",
                "WARNING": "yellow",
                "ERROR": "red",
                "CRITICAL": "bold_red",
            },
        )

    def debug(self, message: str) -> None:
        """Log msg with severity 'DEBUG'.

        :Arg
         - message: Log message
        """
        self.logger.debug(message)

    def info(self, message: str) -> None:
        """Log msg with severity 'INFO'.

        :Arg
         - message: Log message
        """
        self.logger.info(message)

    def warning(self, message: str) -> None:
        """Log msg with severity 'WARNING'.

        :Arg
         - message: log message
        """
        self.logger.warning(message)

    def error(self, message: str) -> None:
        """Log msg with severity 'ERROR'.

        :Arg
         - message: log message
        """
        self.logger.error(message)

    def critical(self, message: str) -> None:
        """Log msg with severity 'CRITICAL'.

        :Arg
         - message: log message
        """
        self.logger.critical(message)

    def close(self) -> None:
        """Logger close."""
        self.logger.disabled = True
