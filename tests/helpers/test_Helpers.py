from sporttracker.helpers.Helpers import format_file_size, format_percentage


class TestHelpers:
    def test_format_percentage_no_previous_value_should_return_infinity(self):
        assert format_percentage(0, 15) == '∞ %'

    def test_format_percentage_no_previous_and_current_value_should_return_0(self):
        assert format_percentage(0, 0) == '0 %'

    def test_format_percentage_increase(self):
        assert format_percentage(100, 150) == '50 %'

    def test_format_percentage_decrease(self):
        assert format_percentage(150, 100) == '33 %'

    def test_format_percentage_no_change(self):
        assert format_percentage(100, 100) == '0 %'

    def test_format_percentage_no_vales(self):
        assert format_percentage(0, 0) == '0 %'

    def test_format_file_size_none(self):
        assert format_file_size(None) == '-'

    def test_format_file_size_bytes(self):
        assert format_file_size(0) == '0 B'
        assert format_file_size(1023) == '1023 B'

    def test_format_file_size_kilobytes(self):
        assert format_file_size(1024) == '1.0 KB'
        assert format_file_size(1536) == '1.5 KB'

    def test_format_file_size_megabytes(self):
        assert format_file_size(1024 * 1024) == '1.0 MB'

    def test_format_file_size_gigabytes(self):
        assert format_file_size(1024 * 1024 * 1024) == '1.0 GB'
