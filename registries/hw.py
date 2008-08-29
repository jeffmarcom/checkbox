#
# Copyright (c) 2008 Canonical
#
# Written by Marc Tardif <marc@interunion.ca>
#
# This file is part of Checkbox.
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
import os
import re
import logging

from checkbox.lib.cache import cache

from checkbox.registries.command import CommandRegistry
from checkbox.registries.data import DataRegistry
from checkbox.registries.map import MapRegistry


class DeviceRegistry(DataRegistry):
    """Registry for HW device information.

    Each item contained in this registry consists of the properties of
    the corresponding HW device.
    """

    @cache
    def items(self):
        items = []
        lines = []

        id = status = depth = None
        for line in self.split("\n"):
            if not line:
                continue

            match = re.match(r"(\s+(\*-)?)(.+)", line)
            if not match:
                raise Exception, "Invalid line: %s" % line

            space = len(match.group(1))
            if depth is None:
                depth = space

            if space > depth:
                lines.append(line)
            elif match.group(2) is not None:
                if id is not None:
                    value = DeviceRegistry(None, "\n".join(lines))
                    lines = []

                    items.append((id, value))
                    items.append(("status", status))

                node = match.group(3)
                match = re.match(r"([^\s]+)( [A-Z]+)?", node)
                if not match:
                    raise Exception, "Invalid node: %s" % node

                id = match.group(1)
                status = match.group(2)
            else:
                (key, value) = match.group(3).split(": ", 1)
                key = key.replace(" ", "_")

                # Parse potential list or dict values
                values = value.split(" ")
                if key == "product":
                    match = re.search(r"(.*) \[[0-9A-F]{1,4}:([0-9A-F]{1,4})\]$",
                        value)
                    if match:
                        value = match.group(1)
                        items.append(("product_id", int(match.group(2), 16)))
                elif key == "vendor":
                    match = re.search(r"(.*) \[([0-9A-F]{1,4})\]$", value)
                    if match:
                        value = match.group(1)
                        items.append(("vendor_id", int(match.group(2), 16)))
                elif key.endswith("s"):
                    value = values
                elif not [v for v in values if not "=" in v]:
                    value = dict((v.split("=") for v in values))
                    value = MapRegistry(None, value)

                items.append((key, value))

     
        if lines:
            value = DeviceRegistry(None, "\n".join(lines))
            items.append((id, value))

        return items


class HwRegistry(CommandRegistry):
    """Registry for HW information.

    Each item contained in this registry consists of the hardware id as
    key and the corresponding device registry as value.
    """

    optional_attributes = CommandRegistry.optional_attributes + ["version"]

    @cache
    def __str__(self):
        logging.info("Running command: %s", self.config.version)
        version = os.popen(self.config.version).read().strip()
        numbers = version.split(".")
        if len(numbers) == 3 \
           and numbers[0] == "B" \
           and int(numbers[1]) == 2 \
           and int(numbers[2]) < 13:
            self.command = self.command.replace(" -numeric", "")

        return super(HwRegistry, self).__str__()

    @cache
    def items(self):
        lines = self.split("\n")

        key = lines.pop(0)
        value = DeviceRegistry(None, "\n".join(lines))

        return [(key, value)]


factory = HwRegistry