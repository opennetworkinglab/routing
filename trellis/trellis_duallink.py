#!/usr/bin/python

import sys
sys.path.append('..')
from mininet.topo import Topo
from mininet.net import Mininet
from mininet.cli import CLI
from mininet.log import setLogLevel
from mininet.node import RemoteController, OVSBridge, Host, OVSSwitch
from mininet.nodelib import NAT
from ipaddress import ip_network
from routinglib import BgpRouter
from routinglib import RoutedHost, RoutedHost6
from trellislib import DhcpClient, Dhcp6Client, DhcpRelay, DhcpServer, Dhcp6Server
from trellislib import get_mininet, parse_trellis_args, set_up_zebra_config
from functools import partial

class Trellis( Topo ):
    "Trellis dual-link topology"

    def __init__( self, *args, **kwargs ):
        Topo.__init__( self, *args, **kwargs )

        # Spines
        s226 = self.addSwitch('s226', dpid='226')
        s227 = self.addSwitch('s227', dpid='227')

        # Leaves
        s204 = self.addSwitch('s204', dpid='204')
        s205 = self.addSwitch('s205', dpid='205')

        # Switch Links - dual-link
        self.addLink(s226, s204)
        self.addLink(s226, s204)

        self.addLink(s226, s205)
        self.addLink(s226, s205)

        self.addLink(s227, s204)
        self.addLink(s227, s204)

        self.addLink(s227, s205)
        self.addLink(s227, s205)

        # NOTE avoid using 10.0.1.0/24 which is the default subnet of quaggas
        # NOTE avoid using 00:00:00:00:00:xx which is the default mac of host behind upstream router
        # IPv4 Hosts
        h1 = self.addHost('h1', cls=DhcpClient, mac='00:aa:00:00:00:01')
        h2 = self.addHost('h2', cls=DhcpClient, mac='00:aa:00:00:00:02')
        h3 = self.addHost('h3', cls=DhcpClient, mac='00:aa:00:00:00:03')
        h4 = self.addHost('h4', cls=DhcpClient, mac='00:aa:00:00:00:04')
        self.addLink(h1, s204)
        self.addLink(h2, s204)
        self.addLink(h3, s205)
        self.addLink(h4, s205)

        # IPv6 Hosts
        h1v6 = self.addHost('h1v6', cls=Dhcp6Client, mac='00:bb:00:00:00:01')
        h2v6 = self.addHost('h2v6', cls=Dhcp6Client, mac='00:bb:00:00:00:02')
        h3v6 = self.addHost('h3v6', cls=Dhcp6Client, mac='00:bb:00:00:00:03')
        h4v6 = self.addHost('h4v6', cls=Dhcp6Client, mac='00:bb:00:00:00:04')
        self.addLink(h1v6, s204)
        self.addLink(h2v6, s204)
        self.addLink(h3v6, s205)
        self.addLink(h4v6, s205)

        # DHCP server
        dhcp = self.addHost('dhcp', cls=DhcpServer, mac='00:99:00:00:00:01', ips=['10.0.3.253/24'], gateway='10.0.3.254')

        # DHCPv6 server
        dhcp6 = self.addHost('dhcp6', cls=Dhcp6Server, mac='00:99:66:00:00:01', ips=['2000::3fd/120'], gateway='2000::3ff')

        # Data plane switch (for DHCP servers)
        cs1 = self.addSwitch('cs1', cls=OVSBridge)
        self.addLink(cs1, s205)
        self.addLink(dhcp, cs1)
        self.addLink(dhcp6, cs1)

        # Control plane switch (for quagga fpm)
        cs0 = self.addSwitch('cs0', cls=OVSBridge)

        # Control plane NAT (for quagga fpm)
        nat = self.addHost('nat', cls=NAT,
                           ip='172.16.0.1/24',
                           subnet=str(ip_network(u'172.16.0.0/24')), inNamespace=False)
        self.addLink(cs0, nat)

        # Internal Quagga bgp1
        intfs = {'bgp1-eth0': {'ipAddrs': ['10.0.1.2/24', '2000::102/120'], 'mac': '00:88:00:00:00:02'},
                 'bgp1-eth1': {'ipAddrs': ['172.16.0.2/24']}}
        bgp1 = self.addHost('bgp1', cls=BgpRouter,
                            interfaces=intfs,
                            quaggaConfFile='./bgpdbgp1.conf',
                            zebraConfFile='./zebradbgp1.conf')
        self.addLink(bgp1, s205)
        self.addLink(bgp1, cs0)

        # External Quagga r1
        intfs = {'r1-eth0': {'ipAddrs': ['10.0.1.1/24', '2000::101/120'], 'mac': '00:88:00:00:00:01'},
                 'r1-eth1': {'ipAddrs': ['10.0.99.1/16']},
                 'r1-eth2': {'ipAddrs': ['2000::9901/120']}}
        r1 = self.addHost('r1', cls=BgpRouter,
                            interfaces=intfs,
                            quaggaConfFile='./bgpdr1.conf')
        self.addLink(r1, s205)

        # External IPv4 Host behind r1
        rh1 = self.addHost('rh1', cls=RoutedHost, ips=['10.0.99.2/24'], gateway='10.0.99.1')
        self.addLink(r1, rh1)

        # External IPv6 Host behind r1
        rh1v6 = self.addHost('rh1v6', cls=RoutedHost, ips=['2000::9902/120'], gateway='2000::9901')
        self.addLink(r1, rh1v6)

topos = { 'trellis' : Trellis }

if __name__ == "__main__":
    setLogLevel('debug')
    topo = Trellis()
    switch = partial(OVSSwitch, protocols='OpenFlow13')
    arguments = parse_trellis_args()
    set_up_zebra_config(arguments.controllers)
    net = get_mininet(arguments, topo, switch)

    net.start()
    CLI(net)
    net.stop()
