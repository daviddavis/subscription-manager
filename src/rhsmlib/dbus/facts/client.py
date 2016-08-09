#!/usr/bin/python
#
# Client DBus proxy for rhsm facts service
#
# Copyright (c) 2010-2016 Red Hat, Inc.
#
# This software is licensed to you under the GNU General Public License,
# version 2 (GPLv2). There is NO WARRANTY for this software, express or
# implied, including the implied warranties of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. You should have received a copy of GPLv2
# along with this software; if not, see
# http://www.gnu.org/licenses/old-licenses/gpl-2.0.txt.
#
# Red Hat trademarks are not licensed under GPLv2. No permission is
# granted to use or replicate Red Hat trademarks that are incorporated
# in this software or its documentation.
#

import logging
import dbus.mainloop.glib

# from rhsmlib.dbus import gi_kluge
# gi_kluge.kluge_it()

# TODO: This is very glib2/dbus-python based. That is likely a requirement
#       for the services, but it may be worthwhile to use something more
#       modern for the client (ie, GIO based dbus support).

# TODO: maybe common.constants should just import all the constants

# FIXME: This makes client code depend on the services code being installed
#        (which it will be, but...)
from rhsmlib.dbus.facts import constants as facts_constants

log = logging.getLogger(__name__)


class FactsClientAuthenticationError(Exception):
    def __init__(self, *args, **kwargs):
        action_id = kwargs.pop("action_id")
        super(FactsClientAuthenticationError, self).__init__(*args, **kwargs)
        log.debug("FactsClientAuthenticationError created for %s", action_id)
        self.action_id = action_id


class FactsClient(object):
    bus_name = facts_constants.FACTS_DBUS_NAME
    object_path = facts_constants.FACTS_DBUS_PATH
    interface_name = facts_constants.FACTS_DBUS_INTERFACE

    def __init__(self, bus=None, bus_name=None, object_path=None, interface_name=None):
        # use default mainloop for dbus
        dbus.mainloop.glib.threads_init()
        dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)

        self.bus = bus or dbus.SystemBus()

        if bus_name:
            self.bus_name = bus_name

        if object_path:
            self.object_path = object_path

        if interface_name:
            self.interface_name = interface_name

        self.dbus_proxy_object = self.bus.get_object(self.bus_name, self.object_path,
            follow_name_owner_changes=True)

        self.interface = dbus.Interface(self.dbus_proxy_object,
            dbus_interface=self.interface_name)

        self.props_interface = dbus.Interface(self.dbus_proxy_object,
            dbus_interface=dbus.PROPERTIES_IFACE)

        self.interface.connect_to_signal("PropertiesChanged", self._on_properties_changed,
            dbus_interface=dbus.PROPERTIES_IFACE,
            sender_keyword='sender', destination_keyword='destination',
            interface_keyword='interface', member_keyword='member',
            path_keyword='path')

        self.bus.call_on_disconnection(self._on_bus_disconnect)
        self.interface.connect_to_signal("ServiceStarted", self._on_service_started,
            sender_keyword='sender', destination_keyword='destination',
            interface_keyword='interface', member_keyword='member',
            path_keyword='path')

    def GetFacts(self, *args, **kwargs):
        log.debug("GetFacts pre")
        ret = self.interface.GetFacts(*args, **kwargs)
        return ret

    def GetAll(self, *args, **kwargs):
        log.debug("GetAll")
        ret = self.props_interface.GetAll(facts_constants.FACTS_DBUS_INTERFACE,
                                          *args, **kwargs)
        log.debug("GetAll res=%s", ret)
        return ret

    def Get(self, property_name):
        log.debug("Get %s", property_name)
        ret = self.props_interface.Get(facts_constants.FACTS_DBUS_INTERFACE,
                                       property_name=property_name)
        return ret

    def signal_handler(self, *args, **kwargs):
        log.debug("signal_handler args=%s kwargs=%s", args, kwargs)

    def _on_properties_changed(self, *args, **kwargs):
        log.debug("PropertiesChanged")
        self.signal_handler(*args, **kwargs)

    def _on_name_owner_changed(self, *args, **kwargs):
        log.debug("NameOwnerChanged")
        self.signal_handler(*args, **kwargs)

    def _on_bus_disconnect(self, connection):
        self.dbus_proxy_object = None
        log.debug("disconnected")

    def _on_service_started(self, *args, **kwargs):
        log.debug("ServiceStarted")
        self.signal_handler(*args, **kwargs)
