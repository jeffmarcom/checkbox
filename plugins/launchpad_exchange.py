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
import time
import pprint
import bz2
import logging

from gettext import gettext as _
from socket import gethostname
from StringIO import StringIO

from checkbox.lib.transport import HTTPTransport

from checkbox.log import format_delta
from checkbox.plugin import Plugin


class LaunchpadExchange(Plugin):

    required_attributes = ["transport_url", "timeout"]

    def register(self, manager):
        super(LaunchpadExchange, self).register(manager)
        self._headers = {}
        self._form = {
            "field.private": False,
            "field.contactable": False,
            "field.live_cd": False,
            "field.format": u'VERSION_1',
            "field.actions.upload": u'Upload'}

        for (rt, rh) in [
             ("report-architecture", self.report_architecture),
             ("report-client", self.report_client),
             ("report-datetime", self.report_datetime),
             ("report-distribution", self.report_distribution),
             ("report-submission_id", self.report_submission_id),
             ("report-system_id", self.report_system_id),
             ("exchange-report", self.exchange_report),
             ("exchange", self.exchange)]:
            self._manager.reactor.call_on(rt, rh)

    def report_architecture(self, message):
        self._form["field.architecture"] = message

    def report_client(self, message):
        user_agent = "%s/%s" % (message["name"], message["version"])
        self._headers["User-Agent"] = user_agent

    def report_datetime(self, message):
        self._form["field.date_created"] = message

    def report_distribution(self, message):
        self._form["field.distribution"] = message.distributor_id
        self._form["field.distroseries"] = message.release

    def report_submission_id(self, message):
        self._form["field.submission_key"] = message

    def report_system_id(self, message):
        self._form["field.system"] = message

    def exchange_report(self, message):
        self._report = message

    def exchange(self, email):
        # Encode form data
        form = {"field.emailaddress": email}
        for field, value in self._form.items():
            form[field] = str(value).encode("UTF-8")

        # Compress and add payload to form
        payload = open(self._report, "r").read()
        compressed_payload = bz2.compress(payload)
        descriptor = StringIO(compressed_payload)
        descriptor.name = '%s.xml.bz2' % str(gethostname())
        descriptor.size = len(compressed_payload)
        form["field.submission_data"] = descriptor

        if logging.getLogger().getEffectiveLevel() <= logging.DEBUG:
            logging.debug("Uncompressed payload length: %d", len(payload))

        self._manager.set_error()
        transport = HTTPTransport(self.config.transport_url)

        start_time = time.time()
        response = transport.exchange(form, self._headers,
            timeout=int(self.config.timeout))
        end_time = time.time()

        if not response:
            self._manager.set_error(_("""\
Failed to contact server. Please try
again or upload the following file:
%s

directly to the system database:
https://launchpad.net/+hwdb/+submit""") % os.path.abspath(self._report))
            return
        elif response.status != 200:
            self._manager.set_error(_("Failed to upload to server,\n"
                "please try again later."))
            return

        if logging.getLogger().getEffectiveLevel() <= logging.DEBUG:
            logging.debug("Response headers:\n%s",
                pprint.pformat(response.getheaders()))

        header = response.getheader("x-launchpad-hwdb-submission")
        if not header:
            self._manager.set_error(_("Information not posted to Launchpad."))
        elif "Error" in header:
            # HACK: this should return a useful error message
            self._manager.set_error(header)
            logging.error(header)
        else:
            text = response.read()
            logging.info("Sent %d bytes and received %d bytes in %s.",
                descriptor.size, len(text), format_delta(end_time - start_time))


factory = LaunchpadExchange
