from sporttracker.helpers.Helpers import format_percentage


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
