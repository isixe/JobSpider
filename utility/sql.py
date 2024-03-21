"""There are some utility functions for SQL operations."""

import sqlite3
from pathlib import Path
from typing import Any

from spider import logger


def execute_sql_command(
    sql: str, path: str | Path, values: list[Any] | None | dict = None
) -> None | list[tuple]:
    """Execute a SQL command on the database."""
    try:
        with sqlite3.connect(str(path)) as conn:
            cursor = conn.cursor()

            if values is None:
                cursor.execute(sql)
                return (
                    cursor.fetchall()
                    if sql.strip().upper().startswith("SELECT")
                    else None
                )

            if sql.strip().upper().startswith("INSERT") and isinstance(values, list):
                cursor.executemany(sql, values)
                logger.info(f"Inserted {len(values)} records")
            elif sql.strip().upper().startswith("INSERT") and isinstance(values, dict):
                cursor.execute(sql, values)
            else:
                cursor.execute(sql, values)

            return (
                cursor.fetchall() if sql.strip().upper().startswith("SELECT") else None
            )

    except sqlite3.IntegrityError:
        logger.warning("SQL integrity error, not unique value")
    except sqlite3.Error as e:
        logger.warning(f"SQL execution failure of SQLite: {e}")
        raise

    return None
