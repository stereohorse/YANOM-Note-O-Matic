import config

import pytest
import report


@pytest.mark.parametrize(
    'conversion_count, message, expected', [
        (0, 'word', ''),
        (1, 'word', '1 word'),
        (2, 'word', '2 words')
    ]
)
def test_print_result_if_any(conversion_count, message, expected):
    result = report.get_result_as_string(conversion_count, message)

    assert result == expected


def test_log_results(caplog):
    report_generator = report.Report('fake_note_converter')
    report_generator._report = 'This is a report'

    caplog.clear()
    report_generator.log_results()

    assert 'This is a report' in caplog.records[0].message


@pytest.mark.parametrize(
    'silent, report_content, expected', [
        (True, 'This is a report', ''),
        (False, 'This is a report', 'This is a report\n'),
    ]
)
def test_output_results_if_not_silent_mode_when_in_silent_mode(capsys, silent, report_content, expected):
    config.yanom_globals.is_silent = silent
    report_generator = report.Report('fake_note_converter')
    report_generator._report = report_content
    config.yanom_globals.is_silent = silent

    report_generator.output_results_if_not_silent_mode()
    captured = capsys.readouterr()
    assert captured.out == expected
