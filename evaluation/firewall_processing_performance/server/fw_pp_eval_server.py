import test_server, threading, logging, sys, getopt, signal

from knock_server.definitions.Constants import *
from knock_server.modules.Configuration import config, initialize
from knock_server.modules.Firewall.Firewall import Firewall

number_of_open_ports = 0
firewallHandler = None
serverThread = None
shutdown = False

class ServerThread(threading.Thread):
    def __init__(self, args):
        self.args = args
        threading.Thread.__init__(self)

    def run(self):
        test_server.start(*self.args)

    def stop(self):
        test_server.stop(None, None)

def openSomePorts():
    global firewallHandler, number_of_open_ports, shutdown
    for i in xrange(55000):
        firewallHandler.openPortForClient(i, IP_VERSION.V4, PROTOCOL.TCP, '1.1.1.1')
        number_of_open_ports += 1
        firewallHandler.openPortForClient(i, IP_VERSION.V4, PROTOCOL.UDP, '1.1.1.1')
        number_of_open_ports += 1

        if shutdown:
            return

    closeSomePorts()

def closeSomePorts():
    global firewallHandler, number_of_open_ports, shutdown
    for i in xrange(number_of_open_ports):
        firewallHandler.closePortForClient(i, IP_VERSION.V4, PROTOCOL.TCP, '1.1.1.1')
        number_of_open_ports -= 1
        firewallHandler.closePortForClient(i, IP_VERSION.V4, PROTOCOL.UDP, '1.1.1.1')
        number_of_open_ports -= 1

        if shutdown:
            return

def stop(sig, frame):
    global shutdown
    shutdown = True

    global serverThread
    serverThread.stop()


LOG = logging.getLogger(__name__)

def logProcessingDelay(delay):
    LOG.warn("IPTables Processing Time for chain-size of %s rules was %sms", number_of_open_ports, delay)

def test(udp, delay_compensation):
    initialize()
    config.firewallPolicy = 'none'

    global firewallHandler
    firewallHandler = Firewall(config)
    firewallHandler.startup()

    global serverThread
    serverThread = ServerThread((udp, delay_compensation, logProcessingDelay))
    serverThread.start()

    openSomePorts()

    serverThread.stop()


def usage():
    print "Usage: fw_pp_eval_server.py [-d <delay compensation in ms] <tcp | udp>"
    sys.exit(2)

def parseArguments(argv):
    delay_compensation = 0
    try:
        opts, args = getopt.getopt(argv, "d:")

        for opt, arg in opts:
            if opt in ("-d"):
                delay_compensation = float(arg) / float(1000)

        if len(args) == 1:
            proto = args[0]
        else:
            usage()

    except getopt.GetoptError:
        usage()

    udp = None
    if proto == 'tcp':
        udp = False
    elif proto == 'udp':
        udp = True
    else:
        usage()

    return udp, delay_compensation


if __name__ == '__main__':
    logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.WARNING, stream=sys.stdout)
    signal.signal(signal.SIGTERM, stop)
    signal.signal(signal.SIGINT, stop)
    test(*parseArguments(sys.argv[1:]))