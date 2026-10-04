from dataclasses import dataclass


@dataclass
class Page:
    results: list
    next_cursor: str | None
