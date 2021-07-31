import pytest

import interactive_cli


def test_exit_if_keyboard_interrupt():
    with pytest.raises(KeyboardInterrupt):
        result = interactive_cli._exit_if_keyboard_interrupt({})


def test_exit_if_keyboard_interrupt_not_interrupted():
    interactive_cli._exit_if_keyboard_interrupt({'an_answer': 'here'})
    # no exception raised means worked OK


def test_show_app_title(capsys):
    interactive_cli.show_app_title()

    captured = capsys.readouterr()
    assert '__   __ _    _   _  ___  __  __ \n\\ \\ / // \\  | \\ | |/ _ \\|  \\/  |\n ' in captured.out


def test_what_module_is_this():
    result = interactive_cli.what_module_is_this()
    assert result == 'interactive_cli'

