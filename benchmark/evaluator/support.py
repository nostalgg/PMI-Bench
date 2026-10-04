"""Trusted fixture helpers. Candidate implementations are imported only in Docker."""
import json
import sqlite3
from pathlib import Path


def connect_schema(test):
    connection = sqlite3.connect(':memory:')
    test.addCleanup(connection.close)
    connection.executescript(Path('/submission/schema.sql').read_text())
    return connection


def sample():
    return json.loads(Path('/submission/sample.json').read_text())
