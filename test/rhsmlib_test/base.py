#! /usr/bin/env python
#
# Copyright (c) 2011 Red Hat, Inc.
#
# This software is licensed to you under the GNU General Public
# License as published by the Free Software Foundation; either version
# 2 of the License (GPLv2) or (at your option) any later version.
# There is NO WARRANTY for this software, express or implied,
# including the implied warranties of MERCHANTABILITY,
# NON-INFRINGEMENT, or FITNESS FOR A PARTICULAR PURPOSE. You should
# have received a copy of GPLv2 along with this software; if not, see
# http://www.gnu.org/licenses/old-licenses/gpl-2.0.txt.
#

try:
    import unittest2 as unittest
except ImportError:
    import unittest

import os
import sys
import subprocess
import logging
import time
import signal

from rhsmlib.dbus import service_wrapper, constants
from rhsmlib import import_class  # NOQA Surface this method here and have all tests reference it from here


class DBusObjectTest(unittest.TestCase):
    def setUp(self):
        self.bus_name = constants.BUS_NAME

        if os.geteuid() == 0:
            self.bus_class_name = 'dbus.SystemBus'
        else:
            self.bus_class_name = 'dbus.SessionBus'

        command = ['python', __file__, '-n', self.bus_name, '-b', self.bus_class_name]

        object_classes = self.dbus_objects()
        for clazz in object_classes:
            command.append(clazz.__module__ + "." + clazz.__name__)

        env = os.environ.copy()
        # Set the python path with everything that nose has already loaded
        env['PYTHONPATH'] = ":".join(sys.path)
        self.dbus_process = subprocess.Popen(command, env=env)
        time.sleep(0.5)

        self.postServerSetUp()

    def tearDown(self):
        os.kill(self.dbus_process.pid, signal.SIGTERM)
        time.sleep(0.2)

    def dbus_objects(self):
        raise NotImplementedError('Subclasses should define what DBus objects to test')

    def postServerSetUp(self):
        # Subclasses are free to implement this method to create dbus proxies for testing
        pass


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG, format="%(levelname)5s [%(name)s:%(lineno)s] %(message)s")
    log = logging.getLogger('')
    log.setLevel(logging.INFO)

    try:
        sys.exit(service_wrapper.main(sys.argv))
    except Exception:
        log.exception("DBus service startup failed")
