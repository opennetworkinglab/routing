#!/usr/bin/python

import sys
sys.path.append('..')
from mininet.topo import Topo
from mininet.net import Mininet
from mininet.cli import CLI
from mininet.log import setLogLevel
from mininet.node import RemoteController, OVSBridge, Host, OVSSwitch
from mininet.link import TCLink
from mininet.nodelib import NAT
from ipaddress import ip_network
from routinglib import BgpRouter
from routinglib import RoutedHost, RoutedHost6
from trellislib import DhcpClient, Dhcp6Client, DhcpRelay, DhcpServer, Dhcp6Server
from trellislib import DualHomedDhcpClient
from trellislib import get_mininet, parse_trellis_args, set_up_zebra_config
from functools import partial

class Trellis( Topo ):
    "Trellis basic topology"

    def __init__( self, *args, **kwargs ):
        Topo.__init__( self, *args, **kwargs )

        # Spines
        s226 = self.addSwitch('s226', dpid='226')
        s227 = self.addSwitch('s227', dpid='227')

        # Leaves
        s203 = self.addSwitch('s203', dpid='203')
        s204 = self.addSwitch('s204', dpid='204')
        s205 = self.addSwitch('s205', dpid='205')
        s206 = self.addSwitch('s206', dpid='206')

        # Leaf-Spine Links
        self.addLink(s226, s203)
        self.addLink(s226, s203)
        self.addLink(s226, s204)
        self.addLink(s226, s204)
        self.addLink(s226, s205)
        self.addLink(s226, s205)
        self.addLink(s226, s206)
        self.addLink(s226, s206)
        self.addLink(s227, s203)
        self.addLink(s227, s203)
        self.addLink(s227, s204)
        self.addLink(s227, s204)
        self.addLink(s227, s205)
        self.addLink(s227, s205)
        self.addLink(s227, s206)
        self.addLink(s227, s206)

        # Leaf-Leaf Links
        self.addLink(s203, s204)
        self.addLink(s205, s206)

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

        # Dual-homed IPv4 Hosts
        dh1 = self.addHost('dh1', cls=DualHomedDhcpClient, mac='00:cc:00:00:00:01')
        self.addLink(dh1, s204)
        self.addLink(dh1, s203)

        # DHCP server
        dhcp = self.addHost('dhcp', cls=DhcpServer, mac='00:99:00:00:00:01', ips=['10.0.3.253/24'], gateway='10.0.3.254')

        # DHCPv6 server
        dhcp6 = self.addHost('dhcp6', cls=Dhcp6Server, mac='00:99:66:00:00:01', ips=['2000::3fd/120'], gateway='2000::3ff')

        # Control plane switch (for DHCP servers)
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
        intfs = {'bgp1-eth0': [{'ipAddrs': ['10.0.1.2/24', '2000::102/120'], 'mac': '00:88:00:00:00:03', 'vlan': '110'},
                               {'ipAddrs': ['10.0.7.2/24', '2000::702/120'], 'mac': '00:88:00:00:00:03', 'vlan': '170'}],
                 'bgp1-eth1': {'ipAddrs': ['172.16.0.3/24']}}
        bgp1 = self.addHost('bgp1', cls=BgpRouter,
                            interfaces=intfs,
                            quaggaConfFile='./bgpdbgp1.conf',
                            zebraConfFile='./zebradbgp1.conf')
        self.addLink(bgp1, s205)
        self.addLink(bgp1, cs0)

        # Internal Quagga bgp2
        intfs = {'bgp2-eth0': [{'ipAddrs': ['10.0.5.2/24', '2000::502/120'], 'mac': '00:88:00:00:00:04', 'vlan': '150'},
                               {'ipAddrs': ['10.0.6.2/24', '2000::602/120'], 'mac': '00:88:00:00:00:04', 'vlan': '160'}],
                 'bgp2-eth1': {'ipAddrs': ['172.16.0.4/24']}}
        bgp2 = self.addHost('bgp2', cls=BgpRouter,
                            interfaces=intfs,
                            quaggaConfFile='./bgpdbgp2.conf',
                            zebraConfFile='./zebradbgp2.conf')
        self.addLink(bgp2, s206)
        self.addLink(bgp2, cs0)

        # External Quagga r1
        intfs = {'r1-eth0': {'ipAddrs': ['10.0.1.1/24', '2000::101/120'], 'mac': '00:88:00:00:00:01'},
                 'r1-eth1': {'ipAddrs': ['10.0.5.1/24', '2000::501/120'], 'mac': '00:88:00:00:00:11'},
                 'r1-eth2': {'ipAddrs': ['10.0.99.1/16']},
                 'r1-eth3': {'ipAddrs': ['2000::9901/120']},
                 'r1-eth4': {'ipAddrs': ['2000::7701/120']}}
        r1 = self.addHost('r1', cls=BgpRouter,
                            interfaces=intfs,
                            quaggaConfFile='./bgpdr1.conf')
        self.addLink(r1, s205)
        self.addLink(r1, s206)

        # External IPv4 Host behind r1
        rh1 = self.addHost('rh1', cls=RoutedHost, ips=['10.0.99.2/24'], gateway='10.0.99.1')
        self.addLink(r1, rh1)

        # External IPv6 Host behind r1
        rh1v6 = self.addHost('rh1v6', cls=RoutedHost, ips=['2000::9902/120'], gateway='2000::9901')
        self.addLink(r1, rh1v6)

        # Another external IPv6 Host behind r1
        rh11v6 = self.addHost('rh11v6', cls=RoutedHost, ips=['2000::7702/120'], gateway='2000::7701')
        self.addLink(r1, rh11v6)

        # External Quagga r2
        intfs = {'r2-eth0': {'ipAddrs': ['10.0.6.1/24', '2000::601/120'], 'mac': '00:88:00:00:00:02'},
                 'r2-eth1': {'ipAddrs': ['10.0.7.1/24', '2000::701/120'], 'mac': '00:88:00:00:00:22'},
                 'r2-eth2': {'ipAddrs': ['10.0.99.1/16']},
                 'r2-eth3': {'ipAddrs': ['2000::9901/120']},
                 'r2-eth4': {'ipAddrs': ['2000::8801/120']}}
        r2 = self.addHost('r2', cls=BgpRouter,
                            interfaces=intfs,
                            quaggaConfFile='./bgpdr2.conf')
        self.addLink(r2, s206)
        self.addLink(r2, s205)

        # External IPv4 Host behind r2
        rh2 = self.addHost('rh2', cls=RoutedHost, ips=['10.0.99.2/24'], gateway='10.0.99.1')
        self.addLink(r2, rh2)

        # External IPv6 Host behind r2
        rh2v6 = self.addHost('rh126', cls=RoutedHost, ips=['2000::9902/120'], gateway='2000::9901')
        self.addLink(r2, rh2v6)

        # Another external IPv6 Host behind r1
        rh22v6 = self.addHost('rh22v6', cls=RoutedHost, ips=['2000::8802/120'], gateway='2000::8801')
        self.addLink(r2, rh22v6)

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
