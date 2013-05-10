# This file is part of Checkbox.
#
# Copyright 2012, 2013 Canonical Ltd.
# Written by:
#   Zygmunt Krynicki <zygmunt.krynicki@canonical.com>
#
# Checkbox is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Checkbox is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Checkbox.  If not, see <http://www.gnu.org/licenses/>.

"""
:mod:`cloudbox.main` -- command line interface
==============================================
"""

import argparse
import logging
import sys

from plainbox.impl.commands.check_config import CheckConfigCommand
from plainbox.impl.commands.run import RunCommand
from plainbox.impl.commands.special import SpecialCommand

from cloudbox import __version__ as version
from cloudbox.config import CloudBoxConfig
from cloudbox.provider import CloudBoxProvider


logger = logging.getLogger("cloudbox.main")


def main(argv=None):
    """
    cloudbox command line utility
    """
    # Initialize basic logging
    logging.basicConfig(level="WARNING")
    # Load CloudBox configuration
    config = CloudBoxConfig.get()
    # Instantiate the provider class
    provider = CloudBoxProvider()
    # Create the command line parser
    parser = argparse.ArgumentParser(
        prog="cloudbox",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument(
        "-v", "--version", action="version",
        version="{}.{}.{}".format(*version[:3]))
    parser.add_argument(
        "-l", "--log-level", action="store",
        choices=('DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'),
        default='WARNING',
        help=argparse.SUPPRESS)
    # Add sub-parsers for all sub-commands we may need
    subparsers = parser.add_subparsers()
    RunCommand(provider).register_parser(subparsers)
    SpecialCommand(provider).register_parser(subparsers)
    CheckConfigCommand(config).register_parser(subparsers)
    # Parse command line arguments
    ns = parser.parse_args(argv)
    # Update the root logger with the log level selected on command line
    logging.getLogger("").setLevel(ns.log_level)
    # Argh the horrror!
    #
    # Since CPython revision cab204a79e09 (landed for python3.3)
    # http://hg.python.org/cpython/diff/cab204a79e09/Lib/argparse.py
    # the argparse module behaves differently than it did in python3.2
    #
    # In practical terms subparsers are now optional in 3.3 so all of the
    # commands are no longer required parameters.
    #
    # To compensate, on python3.3 and beyond, when the user just runs
    # plainbox without specifying the command, we manually, explicitly do
    # what python3.2 did: call parser.error(_('too few arguments'))
    if (sys.version_info[:2] >= (3, 3)
            and getattr(ns, "command", None) is None):
        parser.error(argparse._("too few arguments"))
    else:
        # Run the command, if any
        return ns.command.invoked(ns)
