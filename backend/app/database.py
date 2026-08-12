from contextlib import contextmanager
from typing import Iterator

import mysql.connector
from mysql.connector import MySQLConnection

from app.config import settings


def get_connection() -> MySQLConnection:
    return mysql.connector.connect(
        host=settings.mysql_host,
        port=settings.mysql_port,
        database=settings.mysql_database,
        user=settings.mysql_user,
        password=settings.mysql_password,
        autocommit=False,
    )


@contextmanager
def db_connection() -> Iterator[MySQLConnection]:
    connection = get_connection()
    try:
        yield connection
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()
