#!/usr/bin/python

import os
import sys
import argparse
sys.path.append('..')

if 'ONOS_ROOT' not in os.environ:
    print "Environment var $ONOS_ROOT not set"
    exit()
else:
    ONOS_ROOT = os.environ["ONOS_ROOT"]
    sys.path.append(ONOS_ROOT + "/tools/dev/mininet")

from mininet.topo import Topo
from mininet.net import Mininet
from mininet.cli import CLI
from mininet.log import setLogLevel
from mininet.node import Host, RemoteController
from routinglib import RoutedHost
from bmv2 import ONOSBmv2Switch

PIPECONF_ID = 'org.onosproject.pipelines.fabric'

class Trellis( Topo ):
    "Trellis basic topology"

    def __init__( self, *args, **kwargs ):
        Topo.__init__( self, *args, **kwargs )

        # Spines
        s226 = self.addSwitch('s226', cls=ONOSBmv2Switch, deviceId='226', grpcPort=55226, pipeconfId=PIPECONF_ID, injectPorts=True)
        s227 = self.addSwitch('s227', cls=ONOSBmv2Switch, deviceId='227', grpcPort=55227, pipeconfId=PIPECONF_ID, injectPorts=True)

        # Leaves
        s204 = self.addSwitch('s204', cls=ONOSBmv2Switch, deviceId='204', grpcPort=55204, pipeconfId=PIPECONF_ID, injectPorts=True)
        s205 = self.addSwitch('s205', cls=ONOSBmv2Switch, deviceId='205', grpcPort=55205, pipeconfId=PIPECONF_ID, injectPorts=True)

        # Switch Links
        self.addLink(s226, s204)
        self.addLink(s226, s205)
        self.addLink(s227, s204)
        self.addLink(s227, s205)

        # NOTE avoid using 10.0.1.0/24 which is the default subnet of quaggas
        # NOTE avoid using 00:00:00:00:00:xx which is the default mac of host behind upstream router
        # IPv4 Hosts
        h1 = self.addHost('h1', cls=RoutedHost, mac='00:aa:00:00:00:01', ips=['10.0.2.1/24'], gateway='10.0.2.254')
        h2 = self.addHost('h2', cls=RoutedHost, mac='00:aa:00:00:00:02', ips=['10.0.2.2/24'], gateway='10.0.2.254')
        h3 = self.addHost('h3', cls=RoutedHost, mac='00:aa:00:00:00:03', ips=['10.0.3.1/24'], gateway='10.0.3.254')
        h4 = self.addHost('h4', cls=RoutedHost, mac='00:aa:00:00:00:04', ips=['10.0.3.2/24'], gateway='10.0.3.254')
        self.addLink(h1, s204)
        self.addLink(h2, s204)
        self.addLink(h3, s205)
        self.addLink(h4, s205)

topos = { 'trellis' : Trellis }

def main(args):
    topo = Trellis()
    controller = RemoteController('c0', ip=args.onos_ip)

    net = Mininet(topo=topo, controller=None)
    net.addController(controller)

    net.start()
    CLI(net)
    net.stop()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description='BMv2 mininet demo script (2 by 2 fabric)')
    parser.add_argument('--onos-ip', help='ONOS-BMv2 controller IP address',
                        type=str, action="store", required=True)
    args = parser.parse_args()
    setLogLevel('debug')

    main(args)
