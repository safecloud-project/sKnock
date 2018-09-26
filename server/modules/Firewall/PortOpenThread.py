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

from threading import Thread

from common.decorators.synchronized import synchronized
from common.definitions.Exceptions import *
from PortCloseThread import PortCloseThread

class PortOpenThread(Thread):

    def __init__(self, lock, runningOpenPortTasks, firewallHandler, ipVersion, protocol, port, addr):
        self.runningOpenPortTasks = runningOpenPortTasks
        self.firewallHandler = firewallHandler
        self.ipVersion = ipVersion
        self.protocol = protocol
        self.port = port
        self.addr = addr
        self.lock = lock
        Thread.__init__(self)


    @synchronized
    def run(self):
        threadTaskHash = hash(str(self.port) + str(self.ipVersion) + self.protocol + self.addr)

        try:
            self.firewallHandler.openPortForClient(self.port, self.ipVersion, self.protocol, self.addr)
            PortCloseThread(self.lock, self.runningOpenPortTasks, self.firewallHandler, self.ipVersion, self.protocol, self.port, self.addr).start()

        except PortAlreadyOpenException:
            self.runningOpenPortTasks.remove(threadTaskHash)
            return
        except:
            self.runningOpenPortTasks.remove(threadTaskHash)
            raise
