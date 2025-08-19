from __future__ import annotations

import enum
import logging
import re
import sys
from dataclasses import dataclass

from sporttracker import Constants

LOGGER = logging.getLogger(Constants.APP_NAME)


class ChangelogEntryType(enum.Enum):
    UNKNOWN = 'UNKNOWN', 'text-bg-dark', 'Unknown', 5
    BREAKING_CHANGE = 'BREAKING_CHANGE', 'text-bg-danger', 'BREAKING', 1
    ADD = 'ADD', 'text-bg-primary', 'Added', 2
    FIX = 'FIX', 'text-bg-success', 'Fixed', 3
    CHORE = 'CHORE', 'text-bg-secondary', 'Updated', 4

    color: str
    display_name: str
    order: int

    def __new__(cls, name: str, color: str, display_name: str, order: int):
        member = object.__new__(cls)
        member._value_ = name
        member.color = color
        member.display_name = display_name
        member.order = order
        return member

    @staticmethod
    def get_by_name(name: str) -> ChangelogEntryType:
        if name == 'add':
            return ChangelogEntryType.ADD
        if name == 'fix':
            return ChangelogEntryType.FIX
        if name == 'chore':
            return ChangelogEntryType.CHORE
        if name == 'BREAKING CHANGE':
            return ChangelogEntryType.BREAKING_CHANGE

        return ChangelogEntryType.UNKNOWN


@dataclass
class ChangelogEntry:
    type: ChangelogEntryType
    description: str
    issue_id: int | None = None


@dataclass
class Release:
    name: str
    date: str
    entries: list[ChangelogEntry]


class ChangelogParser:
    PATTERN_RELEASE = re.compile(r'#\s(\d+\.\d+\.\d+)\s-\s\((.*)\)')
    PATTERN_ENTRY = re.compile(r'-\s(.+?):\s+(.+?)(?:\s+\(#(\d+)\))?$')

    def __init__(self, changelog_path: str) -> None:
        self._changelog_path = changelog_path

    def parse(self) -> list[Release]:
        with open(self._changelog_path, encoding='utf-8') as f:
            lines = f.readlines()

        return self._parse(lines)

    @staticmethod
    def _parse(lines: list[str]) -> list[Release]:
        releases = []

        entries: list[ChangelogEntry] = []
        for line in reversed(lines):
            line = line.strip()
            if not line:
                continue

            if line.startswith('#'):
                match = re.match(ChangelogParser.PATTERN_RELEASE, line)
                if match is None:
                    LOGGER.debug(f'Skipping invalid release line: "{line}"')
                    continue

                sorted_entries = sorted(
                    entries, key=lambda e: (e.type.order, sys.maxsize if e.issue_id is None else e.issue_id)
                )
                releases.append(Release(match.group(1), match.group(2), sorted_entries))
                entries = []
            if line.startswith('-'):
                match = re.match(ChangelogParser.PATTERN_ENTRY, line)
                if match is None:
                    LOGGER.debug(f'Skipping invalid changelog entry line: "{line}"')
                    continue

                changelog_entry_type = ChangelogEntryType.get_by_name(match.group(1))
                issue_id = None if match.group(3) is None else int(match.group(3))
                entries.append(ChangelogEntry(changelog_entry_type, match.group(2), issue_id))

        return list(reversed(releases))


if __name__ == '__main__':
    parser = ChangelogParser(r'/CHANGES.md')
    result = parser.parse()
    print(result)
