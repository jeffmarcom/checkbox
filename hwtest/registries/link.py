#
# Copyright (c) 2008 Canonical
#
# Written by Marc Tardif <marc@interunion.ca>
#
# This file is part of HWTest.
#
# HWTest is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# HWTest is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with HWTest.  If not, see <http://www.gnu.org/licenses/>.
#
from hwtest.registry import Registry


class LinkRegistry(Registry):
    """Registry for links.

    The default behavior is to express the given maps as a tree of items.
    """

    def __init__(self, config, link):
        super(LinkRegistry, self).__init__(config)
        self.link = link

    def __str__(self):
        return str(self.link)

    def items(self):
        items = []
        for k, v in self.link.items():
            if isinstance(v, LinkRegistry):
                continue
            items.append([k, v])

        return items