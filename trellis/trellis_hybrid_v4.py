#!/usr/bin/python
import argparse
import sys
import os
import json
import random
import urllib2
sys.path.append('..')
from mininet.topo import Topo
from mininet.cli import CLI
from mininet.log import setLogLevel
from mininet.node import OVSBridge, OVSSwitch
from mininet.nodelib import NAT
from ipaddress import ip_network
from routinglib import BgpRouter
from routinglib import RoutedHost
from trellislib import DhcpClient, DhcpServer
from trellislib import DualHomedDhcpClient
from trellislib import get_mininet, set_up_zebra_config
from functools import partial

PIPECONF_ID = 'org.onosproject.pipelines.fabric'


class Trellis(Topo):
    """Trellis HAG topology with both OVS and BMV2 switches"""

    p4_cls = None

    def get_p4_switch_args(self, name):
        assert Trellis.p4_cls is not None
        return dict(
            name=name,
            cls=Trellis.p4_cls,
            pipeconf=PIPECONF_ID,
            portcfg=True,
            onosdevid="device:" + name)

    def __init__(self, *args, **kwargs):
        Topo.__init__(self, *args, **kwargs)

        # Spines
        s226 = self.addSwitch(latitude="39", longitude="-105",
                              **self.get_p4_switch_args('bmv2-s226'))
        s227 = self.addSwitch('ovs-s227', dpid='227', latitude="39",longitude="-95")

        # Leaves
        s203 = self.addSwitch('ovs-s203', dpid='203', latitude="35",longitude="-110")
        s204 = self.addSwitch(latitude="35", longitude="-105",
                              **self.get_p4_switch_args('bmv2-s204'))
        s205 = self.addSwitch('ovs-s205', dpid='205', latitude="35",longitude="-95")
        s206 = self.addSwitch('ovs-s206', dpid='206', latitude="35",longitude="-90")

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
        h3 = self.addHost('h3', cls=DhcpClient, mac='00:aa:00:00:00:03')
        h4 = self.addHost('h4', cls=DhcpClient, mac='00:aa:00:00:00:04')
        h5 = self.addHost('h5', cls=DhcpClient, mac='00:aa:00:00:00:05')
        h6 = self.addHost('h6', cls=DhcpClient, mac='00:aa:00:00:00:06')
        self.addLink(h3, s203)
        self.addLink(h4, s204)
        self.addLink(h5, s205)
        self.addLink(h6, s205)

        # Dual-homed IPv4 Host on 203-204
        dh1 = self.addHost('dh1', cls=DualHomedDhcpClient, mac='00:cc:00:00:00:01')
        self.addLink(dh1, s204)
        self.addLink(dh1, s203)

        # Dual-homed IPv4 Host for 205-206
        dh2 = self.addHost('dh2', cls=DualHomedDhcpClient, mac='00:cc:00:00:00:02')
        self.addLink(dh2, s205)
        self.addLink(dh2, s206)

        # DHCP server
        dhcp = self.addHost('dhcp', cls=DhcpServer, mac='00:99:00:00:00:01',
                            ips=['10.0.3.253/24'], gateway='10.0.3.254',
                            configFile='./dhcpd_hybrid_v4.conf')

        # Dataplane L2 plane switch (for DHCP servers)
        cs1 = self.addSwitch('cs1', cls=OVSBridge)
        self.addLink(cs1, s205)
        self.addLink(dhcp, cs1)

        # Control plane switch (for quagga fpm)
        cs0 = self.addSwitch('cs0', cls=OVSBridge)

        # Control plane NAT (for quagga fpm)
        nat = self.addHost('nat', cls=NAT,
                           ip='172.16.0.1/24',
                           subnet=str(ip_network(u'172.16.0.0/24')), inNamespace=False)
        self.addLink(cs0, nat)

        # Internal Quagga bgp1
        """
        intfs = {'bgp1-eth0': [{'ipAddrs': ['10.0.1.2/24', '2000::102/120'], 'mac': '00:88:00:00:00:03', 'vlan': '110'},
                               {'ipAddrs': ['10.0.7.2/24', '2000::702/120'], 'mac': '00:88:00:00:00:03', 'vlan': '170'}],
                 'bgp1-eth1': {'ipAddrs': ['172.16.0.3/24']}}
        """
        intfs = {'bgp1-eth0': {'ipAddrs': ['10.0.1.2/24'], 'mac': '00:88:00:00:00:03', 'vlan': '110'},
                 'bgp1-eth1': {'ipAddrs': ['172.16.0.3/24']}}
        bgp1 = self.addHost('bgp1', cls=BgpRouter,
                            interfaces=intfs,
                            quaggaConfFile='./bgpdbgp1.conf',
                            zebraConfFile='./zebradbgp1.conf')
        self.addLink(bgp1, s205)
        self.addLink(bgp1, cs0)

        # Internal Quagga bgp2
        """
        intfs = {'bgp2-eth0': [{'ipAddrs': ['10.0.5.2/24', '2000::502/120'], 'mac': '00:88:00:00:00:04', 'vlan': '150'},
                               {'ipAddrs': ['10.0.6.2/24', '2000::602/120'], 'mac': '00:88:00:00:00:04', 'vlan': '160'}],
                 'bgp2-eth1': {'ipAddrs': ['172.16.0.4/24']}}
        """
        intfs = {'bgp2-eth0': {'ipAddrs': ['10.0.6.2/24'], 'mac': '00:88:00:00:00:04', 'vlan': '160'},
                 'bgp2-eth1': {'ipAddrs': ['172.16.0.4/24']}}
        bgp2 = self.addHost('bgp2', cls=BgpRouter,
                            interfaces=intfs,
                            quaggaConfFile='./bgpdbgp2.conf',
                            zebraConfFile='./zebradbgp2.conf')
        self.addLink(bgp2, s206)
        self.addLink(bgp2, cs0)

        # External Quagga r1
        intfs = {'r1-eth0': {'ipAddrs': ['10.0.1.1/24'], 'mac': '00:88:00:00:00:01'},
                 'r1-eth1': {'ipAddrs': ['10.0.99.1/16']}}
        r1 = self.addHost('r1', cls=BgpRouter,
                            interfaces=intfs,
                            quaggaConfFile='./bgpdr1.conf')
        self.addLink(r1, s205)
        #self.addLink(r1, s206)

        # External IPv4 Host behind r1
        rh1 = self.addHost('rh1', cls=RoutedHost, ips=['10.0.99.2/24'], gateway='10.0.99.1')
        self.addLink(r1, rh1)

        # External Quagga r2
        intfs = {'r2-eth0': {'ipAddrs': ['10.0.6.1/24'], 'mac': '00:88:00:00:00:02'},
                 'r2-eth1': {'ipAddrs': ['10.0.99.1/16']}}
        r2 = self.addHost('r2', cls=BgpRouter,
                            interfaces=intfs,
                            quaggaConfFile='./bgpdr2.conf')
        self.addLink(r2, s206)
        #self.addLink(r2, s205)

        # External IPv4 Host behind r2
        rh2 = self.addHost('rh2', cls=RoutedHost, ips=['10.0.99.2/24'], gateway='10.0.99.1')
        self.addLink(r2, rh2)

        # ----- Secondary fabric -----

        # Spines(HAG)
        s246 = self.addSwitch(latitude="44", longitude="-105",
                              **self.get_p4_switch_args('bmv2-s246'))
        s247 = self.addSwitch(latitude="44", longitude="-95",
                              **self.get_p4_switch_args('bmv2-s247'))

        # Leaves(DAAS)
        s207 = self.addSwitch('ovs-s207', dpid='207', latitude="47", longitude="-105")
        s208 = self.addSwitch(latitude="47", longitude="-95",
                              **self.get_p4_switch_args('bmv2-s208'))

        # HAG-DAAS Links
        self.addLink(s246, s207)
        self.addLink(s246, s208)
        self.addLink(s247, s207)
        self.addLink(s247, s208)

        # HAG - Spine Links
        self.addLink(s246, s226)
        self.addLink(s247, s227)

        # IPv4 Hosts - RPDs
        h1 = self.addHost('h1', cls=DhcpClient, mac='00:dd:00:00:00:01')
        h2 = self.addHost('h2', cls=DhcpClient, mac='00:dd:00:00:00:02')
        self.addLink(h1, s207)
        self.addLink(h2, s208)


topos = { 'trellis' : Trellis }

class ONOSOVSSwitch( OVSSwitch ):
    """OVSSwitch that generates and pushes config to ONOS"""

    def __init__(self, name, netcfg=True, **kwargs):
        OVSSwitch.__init__(self, name, **kwargs)
        self.netcfg = netcfg in (True, '1', 'true', 'True')
        self.netcfgfile = '/tmp/ovs-%s-netcfg.json' % self.name
        self.onosDeviceId = 'of:%s' % self.dpid
        self.longitude = kwargs['longitude'] if 'longitude' in kwargs else None
        self.latitude = kwargs['latitude'] if 'latitude' in kwargs else None

    @staticmethod
    def controllerIp(controllers):
        try:
            clist = controllers[0].nodes()
        except AttributeError:
            clist = controllers
        assert len(clist) > 0
        return random.choice(clist).IP()

    def start(self, controllers):
        """
        Starts the switch, then notifies ONOS about the new device via Netcfg.
        """
        OVSSwitch.start(self, controllers)

        if not self.netcfg:
            # Do not push config to ONOS.
            return

        controllerIP = self.controllerIp(controllers)

        basicCfg = {
            "name": self.name,
            "driver": "ofdpa-ovs"
        }

        if self.longitude and self.latitude:
            basicCfg["longitude"] = self.longitude
            basicCfg["latitude"] = self.latitude

        cfgData = {
            "devices": {
                self.onosDeviceId: { "basic": basicCfg }
            }
        }
        with open(self.netcfgfile, 'w') as fp:
            json.dump(cfgData, fp, indent=4)

        # Build netcfg URL
        url = 'http://%s:8181/onos/v1/network/configuration/' % controllerIP
        # Instantiate password manager for HTTP auth
        pm = urllib2.HTTPPasswordMgrWithDefaultRealm()
        user = os.environ['ONOS_WEB_USER'] if 'ONOS_WEB_USER' in os.environ else 'onos'
        password = os.environ['ONOS_WEB_PASS'] if 'ONOS_WEB_PASS' in os.environ else 'rocks'
        pm.add_password(None, url, user, password)
        urllib2.install_opener(urllib2.build_opener(urllib2.HTTPBasicAuthHandler(pm)))
        try:
            # Push config data to controller
            req = urllib2.Request(url, json.dumps(cfgData),
                                  {'Content-Type': 'application/json'})
            f = urllib2.urlopen(req)
            print f.read()
            f.close()
        except urllib2.URLError as e:
            warn("*** WARN: unable to push config to ONOS (%s)\n" % e.reason)

if __name__ == "__main__":
    setLogLevel('info')

    parser = argparse.ArgumentParser(description="Trellis Arguments")
    parser.add_argument("-c", "--controllers", help = "Comma Separated List of ONOS controllers",
                        required = True, default = "")
    parser.add_argument("-a", "--p4runtime-agent", help = "P4Runtime agent to use on Bmv2 devices (pi or stratum)",
                        required = False, default = "pi")
    arguments = parser.parse_args()
    agent = arguments.p4runtime_agent

    if agent == "stratum":
        from stratum import ONOSStratumBmv2Switch
        Trellis.p4_cls = ONOSStratumBmv2Switch
    else:
        from bmv2 import ONOSBmv2Switch
        Trellis.p4_cls = ONOSBmv2Switch

    set_up_zebra_config(arguments.controllers)

    topo = Trellis()
    switch = partial(ONOSOVSSwitch, protocols='OpenFlow13')
    net = get_mininet(arguments, topo, switch)

    net.start()
    CLI(net)
    net.stop()
