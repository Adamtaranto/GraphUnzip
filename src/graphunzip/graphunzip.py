#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed May  6 07:42:14 2020

"""
from graphunzip.arg_helpers import parse_args_command
import graphunzip.input_output as io
from graphunzip.run_submodules import run_submodule

import logging
import sys
import time


class CustomFormatter(logging.Formatter):
    """Logging colored formatter, adapted from https://alexandra-zaharia.github.io/posts/make-your-own-custom-color-formatter-with-python-logging"""

    grey = "\x1b[38;21m"
    blue = "\x1b[38;5;39m"
    yellow = "\x1b[38;5;226m"
    red = "\x1b[38;5;196m"
    bold_red = "\x1b[31;1m"
    reset = "\x1b[0m"

    def __init__(self, fmt):
        super().__init__()
        self.fmt = fmt
        self.FORMATS = {
            logging.DEBUG: self.grey + self.fmt + self.reset,
            logging.INFO: self.blue + self.fmt + self.reset,
            logging.WARNING: self.yellow + self.fmt + self.reset,
            logging.ERROR: self.red + self.fmt + self.reset,
            logging.CRITICAL: self.bold_red + self.fmt + self.reset,
        }

    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt)
        return formatter.format(record)


def main():
    # Set up logging
    fmt = "%(asctime)s | %(levelname)8s | %(module)s:%(lineno)s:%(funcName)20s() | %(message)s"
    handler_sh = logging.StreamHandler(sys.stdout)
    handler_sh.setFormatter(CustomFormatter(fmt))
    logging.basicConfig(format=fmt, level=logging.INFO, handlers=[handler_sh])

    # Fetch sub-module command
    args_command = parse_args_command()
    command = args_command.command

    # Start time
    starttime = time.time()

    run_submodule(command)

    logging.info(f"Finished in {(time.time() - starttime):.2f} seconds")


if __name__ == "__main__":
    main()
