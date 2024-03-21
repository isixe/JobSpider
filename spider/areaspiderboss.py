"""This is a area spider of Boss."""

import requests

from utility.path import AREABOSS_SQLITE_FILE_PATH
from utility.sql import execute_sql_command


class AreaSpiderBoss:
    """Area spider of Boss."""

    def __init__(self) -> None:
        """Init."""
        self.url = "https://www.zhipin.com/wapi/zpCommon/data/cityGroup.json"
        self.html = requests.get(self.url, timeout=10).json()

    def _get_all_area_codes(self) -> dict[str, str]:
        """Get all area codes."""
        area = {}
        for city_group in self.html["zpData"]["cityGroup"]:
            for city in city_group["cityList"]:
                area[city["name"]] = city["code"]
        return area

    def start(self) -> None:
        """Create and save the area codes to db."""
        sql_table = """
            CREATE TABLE IF NOT EXISTS areaboss (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT,
                code TEXT
            )
        """
        execute_sql_command(sql_table, AREABOSS_SQLITE_FILE_PATH)

        sql = """
            INSERT INTO areaboss (name, code) VALUES (?, ?)
        """
        area = self._get_all_area_codes()
        execute_sql_command(
            sql,
            AREABOSS_SQLITE_FILE_PATH,
            [(name, code) for name, code in area.items()],  # noqa: C416
        )


def start() -> None:
    """Start the spider."""
    AreaSpiderBoss().start()
