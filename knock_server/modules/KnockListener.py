# Copyright (c) 2015 Daniel Sel
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

from ProcessRequestThread import ProcessRequestThread
from knock_server.definitions import Constants

logger = logging.getLogger(__name__)

class KnockListener:

    def __init__(self, cryptoEngine, firewallHandler):
        self.cryptoEngine = cryptoEngine
        self.firewallHandler = firewallHandler
        self.runningPortOpenTasks = list()
        self.udpsocket = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_UDP)
        logger.debug("Socket initialized")

    def processPossibleKnockPackets(self):
        while True:
            packet, source = self.udpsocket.recvfrom(2048)
            source_ip = source[0]

            ipVersionLengthByte = struct.unpack('!B', packet[0])
            ipVersion = ipVersionLengthByte[0] >> 4
            udpHeaderLength = 8;

            if ipVersion == Constants.IP_VERSION.V4:
                ipHeaderLength = (ipVersionLengthByte[0] & 0xF) * 4
            elif ipVersion == Constants.IP_VERSION.V6:
                ipHeaderLength = 40
            else:
                continue

            udpHeader = packet[ipHeaderLength:ipHeaderLength + udpHeaderLength]

            lengthByte = struct.unpack('!H', udpHeader[4:6])
            payloadLength = lengthByte[0] - udpHeaderLength

            isPossibleKnockPacket = payloadLength >= Constants.KNOCKPACKET_MIN_LENGTH

            if isPossibleKnockPacket:
                payload = packet[ipHeaderLength + udpHeaderLength : ipHeaderLength + udpHeaderLength + payloadLength]

                knockId = struct.unpack('!c', payload[0])[0]
                isPossibleKnockPacket = knockId == Constants.KNOCK_ID

            if isPossibleKnockPacket:
                knockVersion = struct.unpack('!BBB', payload[1:4])
                isPossibleKnockPacket = knockVersion <= Constants.KNOCK_VERSION

            if isPossibleKnockPacket:
                ProcessRequestThread(self.cryptoEngine, self.firewallHandler, self.runningPortOpenTasks, ipVersion, source_ip, payload[4:]).start()