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

import logging
import socket
import struct
from threading import Thread
from common.definitions.Constants import IP_VERSION, KNOCK_ID, KNOCK_VERSION
import ProcessRequestThread

LOG = logging.getLogger(__name__)
ETHERNET_HEADER_LENGTH = 14
UDP_HEADER_LENGTH = 8


class NewPacketThread(Thread):

    def __init__(self, knockProcessor, packet):
        self.knockProcessor = knockProcessor
        self.packet = packet
        Thread.__init__(self)

    def run(self):
        # Skip Ethernet Hedaer
        packet = self.packet[ETHERNET_HEADER_LENGTH:]
        # Determine IP version
        ipVersionLengthByte = struct.unpack('!B', packet[0])[0]
        ipVersion = ipVersionLengthByte >> 4
        if ipVersion == IP_VERSION.V4:
            ipProtocol = struct.unpack('!B', packet[9])[0]
            if not ipProtocol == socket.IPPROTO_UDP:
                return
            ipHeaderLength = (ipVersionLengthByte & 0xF) * 4
            sourceIP = socket.inet_ntop(socket.AF_INET, packet[12:16])
        elif ipVersion == IP_VERSION.V6:
            ipProtocol = struct.unpack('!B', packet[6])[0]
            if not ipProtocol == socket.IPPROTO_UDP:
                return
            ipHeaderLength = 40
            sourceIP = socket.inet_ntop(socket.AF_INET6, packet[8:24])
        else:
            LOG.error("Malformed packet received!"
                      " (Or maybe it is just a huge non-IP packet...)")
            return
        # We processed IP Hedaer -> skip
        packet = packet[ipHeaderLength:]
        payloadLength = struct.unpack('!H', packet[4:6])[0] - UDP_HEADER_LENGTH
        # We don't need no ... UDP Header ... or the rest
        packet = packet[UDP_HEADER_LENGTH:UDP_HEADER_LENGTH + payloadLength]
        knockId = struct.unpack('!c', packet[0])[0]
        if knockId != KNOCK_ID:
            return
        knockVersion = struct.unpack('!BBB', packet[1:4])
        if KNOCK_VERSION < knockVersion:
            return
        LOG.debug("Possible port-knocking request received from: %s", sourceIP)
        ProcessRequestThread.ProcessRequestThread(self.knockProcessor,
                                                  ipVersion,
                                                  sourceIP,
                                                  packet[4:]).start()
