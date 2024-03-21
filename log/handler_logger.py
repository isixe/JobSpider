"""Customized log handler."""

import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path

import colorlog

__all__ = ["HandlerLogger"]


class HandlerLogger:
    """Customized log handler."""

    def __init__(self, filename: str) -> None:
        """Initialize the log handler."""
        self.logger = logging.getLogger(__name__)
        self.logger.addHandler(logging.NullHandler())
        self.formatter = self.__init_formatter()
        self.color_formatter = self.__init_color_formatter()
        self.log_handler = self.__init_handler(filename=filename)
        self.console_handler = self.__init_console_handler()
        self.__set_log()
        self.__set_log_handler(self.log_handler)
        self.__set_console_handler(self.console_handler)

    def __set_log(self) -> None:
        self.logger.setLevel(logging.DEBUG)

    def __set_log_handler(self, log_handler: RotatingFileHandler) -> None:
        log_handler.setLevel(logging.INFO)
        log_handler.setFormatter(self.formatter)
        self.logger.addHandler(log_handler)

    def __set_console_handler(self, console_handler: logging.StreamHandler) -> None:
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
        return colorlog.StreamHandler(sys.stdout)

    @staticmethod
    def __init_formatter() -> logging.Formatter:
        log_format = "%(asctime)s [ %(levelname)s ]: %(message)s"
        date_format = "%m/%d/%Y %H:%M:%S %p"
        return logging.Formatter(log_format, date_format)

    @staticmethod
    def __init_color_formatter() -> colorlog.ColoredFormatter:
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

    def debug(self, message: str, *args, **kwargs) -> None:
        """Log debug message."""
        self.logger.debug(message, *args, **kwargs)

    def info(self, message: str, *args, **kwargs) -> None:
        """Log info message."""
        self.logger.info(message, *args, **kwargs)

    def warning(self, message: str, *args, **kwargs) -> None:
        """Log warning message."""
        self.logger.warning(message, *args, **kwargs)

    def error(self, message: str, *args, **kwargs) -> None:
        """Log error message."""
        self.logger.error(message, *args, **kwargs)

    def critical(self, message: str, *args, **kwargs) -> None:
        """Log critical message."""
        self.logger.critical(message, *args, **kwargs)

    def close(self) -> None:
        """Close the logger."""
        for handler in self.logger.handlers:
            handler.close()
            self.logger.removeHandler(handler)
        self.logger.disabled = True
