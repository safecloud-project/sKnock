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


# THIS WRAPPER IS NEEDED TO PROVIDE PRIVILEGES DROPPING OF THE MAIN THREAD

import IPTablesHelper
import signal
import logging

def processFirewallCommands(pipe):
    # Ignore termination signals as the parents sends us termination
    signal.signal(signal.SIGINT, signal.SIG_IGN)
    signal.signal(signal.SIGTERM, signal.SIG_IGN)
    # unset logger
    logging.shutdown()
    while True:
        msg = pipe.recv()
        if msg[1] == 'startService' and len(msg) == 3:
            _startService(msg[2])
            pipe.send(msg[0])
        elif msg[1] == 'openPort' and len(msg) == 6:
            _openPort(msg[2], msg[3], msg[4], msg[5])
            pipe.send(msg[0])
        elif msg[1] == 'closePort' and len(msg) == 6:
            _closePort(msg[2], msg[3], msg[4], msg[5])
            pipe.send(msg[0])
        elif msg[1] == 'stopService' and len(msg) == 2:
            _stopService()
            pipe.send(msg[0])
            pipe.close()
            break
        else:
            pass


def _startService(firewallPolicy):
    IPTablesHelper.backupIPTablesState()
    IPTablesHelper.setupIPTablesPortKnockingChainAndRedirectTraffic(firewallPolicy)
    IPTablesHelper.insertEmergencySSHAccessRule()

def _openPort(port, ipVersion, protocol, addr):
    chain = IPTablesHelper.getIPTablesChainForVersion(ipVersion, IPTablesHelper.IPTABLES_CHAIN_KNOCK)
    rule = IPTablesHelper.getIPTablesRuleForClient(port, ipVersion, protocol, addr)

    IPTablesHelper.deleteIPTablesRuleIgnoringError(rule, chain)
    chain.append_rule(rule)

def _closePort(port, ipVersion, protocol, addr):
    chain = IPTablesHelper.getIPTablesChainForVersion(ipVersion, IPTablesHelper.IPTABLES_CHAIN_KNOCK)
    rule = IPTablesHelper.getIPTablesRuleForClient(port, ipVersion, protocol, addr)

    chain.delete_rule(rule)

def _stopService():
    IPTablesHelper.restoreIPTablesState()
