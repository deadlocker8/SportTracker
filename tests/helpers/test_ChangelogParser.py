from sporttracker.helpers.ChangelogParser import ChangelogParser, Release, ChangelogEntry, ChangelogEntryType


class TestChangelogParser:
    def test_parse_empty_changelog(self):
        result = ChangelogParser._parse([])

        assert len(result) == 0

    def test_parse_release_without_entries(self):
        result = ChangelogParser._parse(['# 1.37.0 - (01.04.25)'])

        assert len(result) == 1
        assert result[0] == Release('1.37.0', '01.04.25', [])

    def test_parse_release_one_entry_of_each_kind(self):
        lines = [
            '# 1.37.0 - (01.04.25)',
            '- BREAKING CHANGE: OMG (#400)',
            '- add: added xyz (#100)',
            '- fix: fixed abc (#200)',
            '- chore: update x (#300)',
        ]

        result = ChangelogParser._parse(lines)

        assert len(result) == 1
        assert result[0].name == '1.37.0'
        assert result[0].date == '01.04.25'
        assert len(result[0].entries) == 4
        assert result[0].entries[0] == ChangelogEntry(ChangelogEntryType.BREAKING_CHANGE, 'OMG', 400)
        assert result[0].entries[1] == ChangelogEntry(ChangelogEntryType.ADD, 'added xyz', 100)
        assert result[0].entries[2] == ChangelogEntry(ChangelogEntryType.FIX, 'fixed abc', 200)
        assert result[0].entries[3] == ChangelogEntry(ChangelogEntryType.CHORE, 'update x', 300)

    def test_parse_release_multiple_entries_check_sort(self):
        lines = [
            '# 1.37.0 - (01.04.25)',
            '- chore: update x (#300)',
            '- fix: fixed abc (#200)',
            '- add: added second (#102)',
            '- add: added xyz (#100)',
            '- BREAKING CHANGE: OMG (#400)',
        ]

        result = ChangelogParser._parse(lines)

        assert len(result) == 1
        assert result[0].name == '1.37.0'
        assert result[0].date == '01.04.25'
        assert len(result[0].entries) == 5
        assert result[0].entries[0] == ChangelogEntry(ChangelogEntryType.BREAKING_CHANGE, 'OMG', 400)
        assert result[0].entries[1] == ChangelogEntry(ChangelogEntryType.ADD, 'added xyz', 100)
        assert result[0].entries[2] == ChangelogEntry(ChangelogEntryType.ADD, 'added second', 102)
        assert result[0].entries[3] == ChangelogEntry(ChangelogEntryType.FIX, 'fixed abc', 200)
        assert result[0].entries[4] == ChangelogEntry(ChangelogEntryType.CHORE, 'update x', 300)

    def test_parse_multiple_releases(self):
        lines = [
            '# 1.37.0 - (01.04.25)',
            '- BREAKING CHANGE: OMG (#400)',
            '- add: added xyz (#100)',
            '- fix: fixed abc (#200)',
            '- chore: update x (#300)',
            '',
            '# 1.36.0 - (30.03.25)',
            '- chore: update z (#150)',
        ]

        result = ChangelogParser._parse(lines)

        assert len(result) == 2
        assert result[0].name == '1.37.0'
        assert result[0].date == '01.04.25'
        assert len(result[0].entries) == 4

        assert result[1].name == '1.36.0'
        assert result[1].date == '30.03.25'
        assert len(result[1].entries) == 1

    def test_parse_without_issue_id(self):
        lines = [
            '# 1.37.0 - (01.04.25)',
            '- add: added xyz',
        ]

        result = ChangelogParser._parse(lines)

        assert len(result) == 1
        assert len(result[0].entries) == 1
        assert result[0].entries[0] == ChangelogEntry(ChangelogEntryType.ADD, 'added xyz', None)

    def test_parse_malformed_lines(self):
        lines = [
            '# 1.37.0',
            '- XYZ: OMG (#ddd)',
        ]

        result = ChangelogParser._parse(lines)

        assert len(result) == 0

    def test_parse_upcoming_releases(self):
        lines = [
            '# 1.37.0 - (XX.XX.XX)',
            '- add: added xyz (#100)',
        ]

        result = ChangelogParser._parse(lines)

        assert len(result) == 1
        assert result[0].name == '1.37.0'
        assert result[0].date == 'XX.XX.XX'
