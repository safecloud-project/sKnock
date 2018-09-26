# Copyright (C) 2015-2016 Daniel Sel
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA 02111-1307
# USA
#

import atexit
import datetime
import logging
import random
import string
import sys
import threading
from multiprocessing import Process, Pipe

from common.modules.Platform import PlatformUtils

import LinuxServiceWrapper
from common.decorators.synchronized import synchronized
from common.definitions.Exceptions import *

LOG = logging.getLogger(__name__)

class Firewall:

    def __init__(self, config):
        self.config = config
        self.platform = PlatformUtils.detectPlatform()
        self.firewallServicePipe, remotePipeEnd = Pipe()
        self.firewallService = None
        self.openPortsList = set()

        if(self.platform == PlatformUtils.LINUX):
            self.firewallService = Process(target=LinuxServiceWrapper.processFirewallCommands, args=((remotePipeEnd),))

        elif self.platform == PlatformUtils.WINDOWS:
            # TODO: implement for windows
            pass

        atexit.register(self.shutdown)

    def startup(self):
        LOG.debug("Starting Firewall handling service...")

        if(self.platform == PlatformUtils.LINUX):
            self.firewallService.start()

        elif self.platform == PlatformUtils.WINDOWS:
            # TODO: implement for windows
            pass

        self._executeTask(["startService", self.config.firewallPolicy])


    def shutdown(self):
        LOG.debug("Stopping Firewall handling service...")

        self._executeTask(["stopService"])
        self.firewallServicePipe.close()

        if(self.platform == PlatformUtils.LINUX):
            self.firewallService.join()

        elif self.platform == PlatformUtils.WINDOWS:
            # TODO: implement for windows
            pass

    def openPortForClient(self, port, ipVersion, protocol, addr):

        openPort = hash(str(port) + str(ipVersion) + protocol + addr)
        if openPort in self.openPortsList:
            LOG.debug('%s port %s for host %s is already open.', protocol, port, addr)
            raise PortAlreadyOpenException

        self._executeTask(['openPort', port, ipVersion, protocol, addr])
        self.openPortsList.add(openPort)
        LOG.info('%s port %s opened for host %s; will be closed in %s seconds.',
                 protocol, port, addr,
                 self.config.PORT_OPEN_DURATION_IN_SECONDS)


    def closePortForClient(self, port, ipVersion, protocol, addr):
        self._executeTask(['closePort', port, ipVersion, protocol, addr])
        self.openPortsList.remove(hash(str(port) + str(ipVersion) + protocol + addr))
        LOG.info('%s port %s closed for host %s.', protocol, port, addr)


    @synchronized
    def _executeTask(self, msg):
        taskId = Firewall._generateRandomTaskId()
        taskMsg = [taskId]
        taskMsg.extend(msg)

        try:
            self.firewallServicePipe.send(taskMsg)
            if self.firewallServicePipe.poll(2):
                if self.firewallServicePipe.recv() != taskId:
                    Firewall._crashRaceCondition()
            else:
                Firewall._crashNotResponding()

        except IOError:
            LOG.error('Firewall handling service not running!')
            LOG.debug('Can\'t execute requested task: %s', msg)


    @staticmethod
    def _generateRandomTaskId():
        return ''.join([random.choice(string.ascii_letters + string.digits) for n in xrange(32)])

    @staticmethod
    def _crashRaceCondition():
        message = "Tasks executed in wrong order - possible race condition or vulnerability!"
        LOG.error(message)
        sys.exit(message)

    @staticmethod
    def _crashNotResponding():
        message = "Firewall service not responding!"
        LOG.error(message)
        sys.exit(message)
