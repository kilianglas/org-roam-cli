from __future__ import annotations

import re
from typing import Any

from pydantic import BaseModel, field_validator


def _strip_elisp_quotes(v: Any) -> Any:
    """Strip surrounding double quotes from elisp-encoded strings."""
    if isinstance(v, str) and len(v) >= 2 and v.startswith('"') and v.endswith('"'):
        return v[1:-1]
    return v


def _parse_elisp_properties(raw: str | None) -> dict[str, str]:
    """Parse elisp alist properties into a dict.

    Handles format like: (("KEY" . "VALUE") ("KEY2" . "VALUE2"))
    """
    if not raw:
        return {}
    props = {}
    for match in re.finditer(r'\("([^"]+)"\s*\.\s*"([^"]*)"\)', raw):
        props[match.group(1)] = match.group(2)
    return props


class Node(BaseModel):
    id: str
    file: str
    level: int
    title: str | None = None
    todo: str | None = None
    properties: dict[str, str] = {}
    olp: str | None = None
    file_title: str | None = None
    tags: list[str] = []
    aliases: list[str] = []
    refs: list[str] = []

    @field_validator("id", "file", "title", "todo", "olp", "file_title", mode="before")
    @classmethod
    def strip_quotes(cls, v: Any) -> Any:
        return _strip_elisp_quotes(v)

    @field_validator("properties", mode="before")
    @classmethod
    def parse_properties(cls, v: Any) -> dict[str, str]:
        if isinstance(v, dict):
            return v
        return _parse_elisp_properties(v)


class Link(BaseModel):
    source_id: str
    source_title: str | None = None
    source_file: str | None = None
    dest_id: str
    dest_title: str | None = None
    dest_file: str | None = None
    link_type: str

    @field_validator(
        "source_id", "source_title", "source_file",
        "dest_id", "dest_title", "dest_file", "link_type",
        mode="before",
    )
    @classmethod
    def strip_quotes(cls, v: Any) -> Any:
        return _strip_elisp_quotes(v)


class SearchResult(BaseModel):
    node: Node
    score: float
