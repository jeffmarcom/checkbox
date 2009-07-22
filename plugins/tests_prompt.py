#
# This file is part of Checkbox.
#
# Copyright 2008 Canonical Ltd.
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
#
from checkbox.lib.iterator import PREV

from checkbox.job import JobIterator, UNINITIATED
from checkbox.plugin import Plugin
from checkbox.properties import String


class TestsPrompt(Plugin):

    # Plugin default for running test types
    plugin_default = String(default="shell")

    # Status default for test types
    status_default = String(default=UNINITIATED)

    def register(self, manager):
        super(TestsPrompt, self).register(manager)
        self._iterator = None
        self._keys = []
        self._tests = {}

        for (rt, rh) in [
             ("report", self.report),
             ("report-test", self.report_test),
             ("prompt-tests", self.prompt_tests)]:
            self._manager.reactor.call_on(rt, rh)

        self._manager.reactor.call_on("prompt-suite-.*", self.prompt_suite_all, -100)

    def prompt_suite_all(self, interface, suite):
        self._iterator = None
        self._keys = []

    def report(self):
        self._manager.reactor.fire("report-tests", self._tests.values())

    def report_test(self, test):
        key = (test["suite"], test["name"],)
        self._keys.append(key)
        if key not in self._tests:
            test.setdefault("plugin", self.plugin_default)
            test.setdefault("status", self.status_default)
            self._tests[key] = test

    def prompt_tests(self, interface, blacklist=[], whitelist=[]):
        if not self._iterator:
            tests = [self._tests[k] for k in self._keys]
            self._iterator = JobIterator(tests, self._manager.registry)
            if interface.direction == PREV:
                self._iterator = self._iterator.last()

        while True:
            try:
                test = self._iterator.go(interface.direction)
            except StopIteration:
                break

            self._manager.reactor.fire("prompt-test-%s" % test["plugin"],
                interface, test)


factory = TestsPrompt