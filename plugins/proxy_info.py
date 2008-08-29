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
from checkbox.lib.environ import add_variable

from checkbox.plugin import Plugin


class ProxyInfo(Plugin):

    optional_attributes = ["http_proxy", "https_proxy"]

    def register(self, manager):
        super(ProxyInfo, self).register(manager)
        self._manager.reactor.call_on("gather", self.gather)

    def gather(self):
        for attribute in self.optional_attributes:
            value = getattr(self.config, attribute)
            if value:
                add_variable(attribute, value)


factory = ProxyInfo