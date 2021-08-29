#!/usr/bin/env python3
""" Parse command line arguments, configure root loggers and initialise the note conversion process """

import argparse
import logging
import logging.handlers as handlers
from pathlib import Path
import sys

import config
from config_data import ConfigData
from helper_functions import find_working_directory
import interactive_cli
from notes_converter import NotesConvertor


def what_module_is_this():
    return __name__


def command_line_parser(args, logger):
    parser = argparse.ArgumentParser(description="YANOM Note-O-Matic notes convertor")

    parser.add_argument('-v', '--version', action='version',
                        version='%(prog)s Version {}'.format(config.yanom_globals.version)
                        )
    parser.add_argument("-s", "--silent", action="store_true",
                        help="No output to console. WILL also use ini file settings.")
    parser.add_argument('--source', nargs='?', default='',
                        help='Sub directory of "data" directory containing one or more files to process, '
                             'or the name of a single file. or an absolute path to a folder or file  '
                             'For example "--source my_html_file.html" or "--source /some_path/my_nsx_files" or '
                             '"--source my_notes", or "--source /some_path/my_nsx_files/my_export.nsx"'
                             'If not provided will search and use "data" folder of the working directory AND '
                             'any of its sub folders. '
                             'When --source is provided it WILL override config.ini setting when '
                             'used with the -i option')
    parser.add_argument('--export', nargs='?', default='',
                        help='Sub directory of "data" directory, or an absolute path to a directory '
                             'that the converted content and attachments will be exported to.  '
                             'For example "--export_notes" or "--source /usr/somewhere/exports/notes" '
                             'If not provided a folder "data" will be used in the working directory.'
                             'When --export is provided it WILL override config.ini setting when '
                             'used with the -i option')
    parser.add_argument("-l", "--log", default='INFO',
                        help="Set the level of program logging. Default = INFO. "
                             "Choices are INFO, DEBUG, WARNING, ERROR, CRITICAL"
                             "Example --log debug or --log INFO")
    group = parser.add_argument_group('Mutually exclusive options. ',
                                      'To use the interactive command line tool for settings '
                                      'DO NOT use -s or -i')
    settings_from_group = group.add_mutually_exclusive_group()
    settings_from_group.add_argument("-i", "--ini", action="store_true",
                                     help="Use config.ini for conversion settings.")
    settings_from_group.add_argument("-c", "--cli", action="store_true",
                                     help="Use interactive command line interface to choose options and settings. "
                                          "This is the default if no argument is provided.")

    command_line_args = vars(parser.parse_args(args))
    logger.info(f"Command line arguments used are '{command_line_args}'")
    return command_line_args


def set_logging_level(log_level: str, logger):
    levels = {
        'critical': logging.CRITICAL,
        'error': logging.ERROR,
        'warn': logging.WARNING,
        'warning': logging.WARNING,
        'info': logging.INFO,
        'debug': logging.DEBUG,
    }
    new_level = levels.get(log_level.lower(), None)

    if new_level is None:
        logger.warning(f'Invalid log level on command line: "{log_level}".  Using INFO level')
        new_level = logging.INFO

    config.yanom_globals.logger_level = new_level


def setup_logging(working_path):
    Path(working_path, 'logs').mkdir(parents=True, exist_ok=True)

    log_filename = f"{working_path}/logs/normal.log"
    error_log_filename = f"{working_path}/logs/error.log"
    debug_log_filename = f"{working_path}/logs/debug.log"
    warning_log_filename = f"{working_path}/logs/warning.log"

    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)

    file_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(name)s - %(message)s')

    logHandler = handlers.RotatingFileHandler(log_filename, maxBytes=2 * 1024 * 1024, backupCount=5)
    logHandler.setLevel(logging.INFO)
    logHandler.setFormatter(file_formatter)

    errorLogHandler = handlers.RotatingFileHandler(error_log_filename, maxBytes=2 * 1024 * 1024, backupCount=5)
    errorLogHandler.setLevel(logging.ERROR)
    errorLogHandler.setFormatter(file_formatter)

    warningLogHandler = handlers.RotatingFileHandler(warning_log_filename, maxBytes=2 * 1024 * 1024, backupCount=5)
    warningLogHandler.setLevel(logging.WARNING)
    warningLogHandler.setFormatter(file_formatter)

    debugLogHandler = handlers.RotatingFileHandler(debug_log_filename, maxBytes=2 * 1024 * 1024, backupCount=5)
    debugLogHandler.setLevel(logging.DEBUG)
    debugLogHandler.setFormatter(file_formatter)
    root_logger.addHandler(debugLogHandler)

    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.CRITICAL)

    root_logger.addHandler(console_handler)
    root_logger.addHandler(logHandler)
    root_logger.addHandler(errorLogHandler)
    root_logger.addHandler(warningLogHandler)

    logger = logging.getLogger(f'{config.yanom_globals.app_name}.{what_module_is_this()}')

    return logger


def main(command_line_sys_argv=sys.argv):
    working_directory, working_directory_message = find_working_directory()

    logger = setup_logging(working_directory)
    logger.info('\n\n\n\n\n\n')
    logger.info(f'YANOM startup - version {config.yanom_globals.version}\n')
    logger.debug(working_directory_message)
    command_line_args = command_line_parser(command_line_sys_argv[1:], logger)
    set_logging_level(command_line_args['log'], logger)

    if command_line_args['silent'] and not command_line_args['ini']:
        command_line_args['ini'] = True

    config.yanom_globals.is_silent = command_line_args['silent']

    run_yanom(command_line_args)


def run_yanom(command_line_args):
    if not command_line_args['silent']:
        interactive_cli.show_app_title()

    config_data = ConfigData(f"config.ini", 'gfm', allow_no_value=True)
    config_data.parse_config_file()

    notes_converter = NotesConvertor(command_line_args, config_data)

    if not command_line_args['ini']:
        while True:
            notes_converter.convert_notes()
    else:
        notes_converter.convert_notes()


def handle_unhandled_exception(exc_type, exc_value, exc_traceback):
    """Handler for unhandled exceptions that will write to the logs"""
    if issubclass(exc_type, KeyboardInterrupt):
        logging.warning("Cancelled by User", exc_info=(exc_type, exc_value, exc_traceback))
        return

    logging.critical("Unhandled exception", exc_info=(exc_type, exc_value, exc_traceback))


sys.excepthook = handle_unhandled_exception

if __name__ == '__main__':
    main()
