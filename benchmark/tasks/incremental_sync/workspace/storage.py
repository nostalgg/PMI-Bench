"""Protected storage/publication contract used by the existing consumer."""
import json
from contextlib import contextmanager
import os
import sqlite3
import tempfile
from pathlib import Path


@contextmanager
def connect_store(directory):
    path = Path(directory) / 'business.sqlite'
    initialize = not path.exists()
    connection = sqlite3.connect(path)
    try:
        if initialize:
            connection.executescript((Path(__file__).parent / 'fixtures' / 'store.sql').read_text())
        with connection:
            yield connection
    finally:
        connection.close()


def read_only_query(connection, filename):
    allowed = {sqlite3.SQLITE_SELECT, sqlite3.SQLITE_READ, sqlite3.SQLITE_FUNCTION}
    connection.set_authorizer(lambda action, *_: sqlite3.SQLITE_OK if action in allowed else sqlite3.SQLITE_DENY)
    try:
        return connection.execute((Path(__file__).parent / filename).read_text()).fetchall()
    finally:
        connection.set_authorizer(None)


def publish_result(result, directory):
    directory = Path(directory)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', dir=directory, delete=False) as stream:
            temporary = stream.name
            json.dump(result, stream, ensure_ascii=False, allow_nan=False)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, directory / 'result.json')
        temporary = None
    finally:
        if temporary is not None:
            Path(temporary).unlink(missing_ok=True)
