#!/usr/bin/python

"""
Libraries for Trellis hosts.
"""

import sys
import time

sys.path.append('..')
from mininet.node import Host, RemoteController
from routinglib import RoutedHost, RoutedHost6, Router
import argparse
from mininet.net import Mininet

class TaggedRoutedHost(RoutedHost):
    """Host that can be configured with multiple IP addresses."""
    def __init__(self, name, ips, gateway, vlan, *args, **kwargs):
        super(RoutedHost, self).__init__(name, *args, **kwargs)
        self.ips = ips
        self.gateway = gateway
        self.vlan = vlan
        self.vlanIntf = None

    def config(self, **kwargs):
        Host.config(self, **kwargs)
        self.vlanIntf = "%s.%s" % (self.defaultIntf(), self.vlan)
        self.cmd('ip -4 addr flush dev %s' % self.defaultIntf())
        self.cmd('ip link add link %s name %s type vlan id %s' % (self.defaultIntf(), self.vlanIntf, self.vlan))
        self.cmd('ip link set up %s' % self.vlanIntf)

        for ip in self.ips:
            self.cmd('ip addr add %s dev %s' % (ip, self.vlanIntf))

        self.cmd('ip route add default via %s' % self.gateway)

        # update the intf name and host's intf map
        self.defaultIntf().name = self.vlanIntf
        self.nameToIntf[self.vlanIntf] = self.defaultIntf()

        disable_offload(self, self.vlanIntf)

    def terminate(self, **kwargs):
        self.cmd('ip link remove link %s' % self.vlanIntf)
        super(TaggedRoutedHost, self).terminate()

class DoubleTaggedRoutedHost(RoutedHost):
    def __init__(self, name, ips, outerVlan, innerVlan, gateway, *args, **kwargs):
        super(RoutedHost, self).__init__(name, *args, **kwargs)
        self.ips = ips
        self.gateway = gateway
        self.innerVlan = innerVlan
        self.outerVlan = outerVlan
        self.innerVlanIntf = None
        self.outerVlanIntf = None

    def config(self, **kwargs):
        Host.config(self, **kwargs)
        self.outerVlanIntf = "%s.%s" % (self.defaultIntf(), self.outerVlan)
        self.outerVlanIntf = self.outerVlanIntf.split("-")[1]
        self.innerVlanIntf = "%s.%s" % (self.outerVlanIntf, self.innerVlan)
        self.cmd('ip -4 addr flush dev %s' % self.defaultIntf())
        self.cmd('ip link add link %s %s type vlan proto 802.1ad id %s' % (self.defaultIntf(), self.outerVlanIntf, self.outerVlan))
        self.cmd('ip link add link %s %s type vlan proto 802.1Q id %s' % (self.outerVlanIntf, self.innerVlanIntf, self.innerVlan))
        self.cmd('ip link set up %s' % self.outerVlanIntf)
        self.cmd('ip link set up %s' % self.innerVlanIntf)

        for ip in self.ips:
            self.cmd('ip addr add %s dev %s' % (ip, self.innerVlanIntf))

        self.cmd('ip route add default via %s' % self.gateway)

        disable_offload(self, self.innerVlanIntf)

    def terminate(self, **kwargs):
        self.cmd('ip link remove link %s' % self.outerVlanIntf)
        self.cmd('ip link remove link %s' % self.innerVlanIntf)
        super(DoubleTaggedRoutedHost, self).terminate()

class DhcpClient(Host):
    def __init__(self, name, *args, **kwargs):
        super(DhcpClient, self).__init__(name, **kwargs)
        self.pidFile = '/run/dhclient-%s.pid' % self.name
        self.leaseFile = '/var/lib/dhcp/dhcpclient-%s.lease' % (self.name, )

    def config(self, **kwargs):
        super(DhcpClient, self).config(**kwargs)
        self.cmd('ip addr flush dev %s' % self.defaultIntf())
        self.cmd('dhclient -q -4 -nw -pf %s -lf %s %s' % (self.pidFile, self.leaseFile, self.defaultIntf()))

        disable_offload(self, self.defaultIntf())

    def terminate(self, **kwargs):
        self.cmd('kill -9 `cat %s`' % self.pidFile)
        self.cmd('rm -rf %s' % self.pidFile)
        super(DhcpClient, self).terminate()

class Dhcp6Client(Host):
    def __init__(self, name, *args, **kwargs):
        super(Dhcp6Client, self).__init__(name, **kwargs)
        self.pidFile = '/run/dhclient-%s.pid' % self.name
        self.leaseFile = '/var/lib/dhcp/dhcpclient6-%s.lease' % (self.name, )

    def config(self, **kwargs):
        super(Dhcp6Client, self).config(**kwargs)
        self.cmd('ip -4 addr flush dev %s' % self.defaultIntf())
        time.sleep(3)
        self.cmd('dhclient -q -6 -nw -pf %s -lf %s %s' % (self.pidFile, self.leaseFile, self.defaultIntf()))

        disable_offload(self, self.defaultIntf())

    def terminate(self, **kwargs):
        self.cmd('kill -9 `cat %s`' % self.pidFile)
        self.cmd('rm -rf %s' % self.pidFile)
        super(Dhcp6Client, self).terminate()

# Client that has on the same interface (eth0) both IPv4 and IPv6 addresses
class Dhcp4and6Client(Host):
    def __init__(self, name, *args, **kwargs):
        super(Dhcp4and6Client, self).__init__(name, **kwargs)
        self.pidFile4 = '/run/dhclient-%s-4.pid' % self.name
        self.pidFile6 = '/run/dhclient-%s-6.pid' % self.name
        self.leaseFile4 = '/var/lib/dhcp/dhcpclient-%s.lease' % (self.name, )
        self.leaseFile6 = '/var/lib/dhcp/dhcpclient6-%s.lease' % (self.name, )

    def config(self, **kwargs):
        super(Dhcp4and6Client, self).config(**kwargs)
        self.cmd('ip addr flush dev %s' % self.defaultIntf())
        self.cmd('dhclient -q -4 -nw -pf %s -lf %s %s' % (self.pidFile4, self.leaseFile4, self.defaultIntf()))

        self.cmd('ip -4 addr flush dev %s' % self.defaultIntf())
        time.sleep(3)
        self.cmd('dhclient -q -6 -nw -pf %s -lf %s %s' % (self.pidFile6, self.leaseFile6, self.defaultIntf()))

        disable_offload(self, self.defaultIntf())

    def terminate(self, **kwargs):
        self.cmd('kill -9 `cat %s`' % self.pidFile4)
        self.cmd('rm -rf %s' % self.pidFile4)
        self.cmd('kill -9 `cat %s`' % self.pidFile6)
        self.cmd('rm -rf %s' % self.pidFile6)
        super(Dhcp4and6Client, self).terminate()

class DhcpServer(RoutedHost):
    binFile = '/usr/sbin/dhcpd'
    pidFile = '/run/dhcp-server-dhcpd.pid'
    configFile = './dhcpd.conf'
    leasesFile = '/var/lib/dhcp/dhcpd.leases'

    def config(self, **kwargs):
        super(DhcpServer, self).config(**kwargs)
        if "configFile" in kwargs:
            self.configFile = kwargs['configFile']
        self.cmd('touch %s' % self.leasesFile)
        self.cmd('%s -q -4 -pf %s -cf %s %s' % (self.binFile, self.pidFile, self.configFile, self.defaultIntf()))

        disable_offload(self, self.defaultIntf())

    def terminate(self, **kwargs):
        self.cmd('kill -9 `cat %s`' % self.pidFile)
        self.cmd('rm -rf %s' % self.pidFile)
        super(DhcpServer, self).terminate()

class Dhcp6Server(RoutedHost6):
    binFile = '/usr/sbin/dhcpd'
    pidFile = '/run/dhcp-server-dhcpd6.pid'
    configFile = './dhcpd6.conf'
    leasesFile = '/var/lib/dhcp/dhcpd6.leases'

    def config(self, **kwargs):
        super(Dhcp6Server, self).config(**kwargs)
        linkLocalAddr = mac_to_ipv6_linklocal(kwargs['mac'])
        self.cmd('ip -6 addr add dev %s scope link %s' % (self.defaultIntf(), linkLocalAddr))
        self.cmd('touch %s' % self.leasesFile)
        self.cmd('%s -q -6 -pf %s -cf %s %s' % (self.binFile, self.pidFile, self.configFile, self.defaultIntf()))

        disable_offload(self, self.defaultIntf())

    def terminate(self, **kwargs):
        self.cmd('kill -9 `cat %s`' % self.pidFile)
        self.cmd('rm -rf %s' % self.pidFile)
        self.cmd('rm -rf  %s' % self.leasesFile)
        super(Dhcp6Server, self).terminate()

class DhcpRelay(Router):
    binFile = '/usr/sbin/dhcrelay'
    pidFile = '/run/dhcp-relay.pid'
    serverIp = None
    gateway = None

    def __init__(self, name, serverIp, gateway, *args, **kwargs):
        super(DhcpRelay, self).__init__(name, **kwargs)
        self.serverIp = serverIp
        self.gateway = gateway

    def config(self, **kwargs):
        super(DhcpRelay, self).config(**kwargs)
        ifacesStr = ' '.join(["-i " + ifaceName for ifaceName in self.interfaces.keys()])
        self.cmd('route add default gw %s' % self.gateway)
        self.cmd('%s -4 -a -pf %s %s %s' % (self.binFile, self.pidFile, ifacesStr, self.serverIp))

        disable_offload(self, ifacesStr)

    def terminate(self, **kwargs):
        self.cmd('kill -9 `cat %s`', self.pidFile)
        self.cmd('rm -rf %s' % self.pidFile)
        super(DhcpRelay, self).terminate()

class TaggedDhcpClient(Host):
    def __init__(self, name, vlan, *args, **kwargs):
        super(TaggedDhcpClient, self).__init__(name, **kwargs)
        self.pidFile = '/run/dhclient-%s.pid' % self.name
        self.vlan = vlan
        self.vlanIntf = None

    def config(self, **kwargs):
        super(TaggedDhcpClient, self).config(**kwargs)
        self.vlanIntf = "%s.%s" % (self.defaultIntf(), self.vlan)
        self.cmd('ip addr flush dev %s' % self.defaultIntf())
        self.cmd('ip link add link %s name %s type vlan id %s' % (self.defaultIntf(), self.vlanIntf, self.vlan))
        self.cmd('ip link set up %s' % self.vlanIntf)
        self.cmd('dhclient -q -4 -nw -pf %s %s' % (self.pidFile, self.vlanIntf))

        disable_offload(self, self.vlanIntf)

    def terminate(self, **kwargs):
        self.cmd('kill -9 `cat %s`' % self.pidFile)
        self.cmd('rm -rf %s' % self.pidFile)
        self.cmd('ip link remove link %s' % self.vlanIntf)
        super(TaggedDhcpClient, self).terminate()

class TaggedDhcpServer(TaggedRoutedHost):
    binFile = '/usr/sbin/dhcpd'
    pidFile = '/run/dhcp-server/dhcpd.pid'
    configFile = './dhcpd.conf'

    def config(self, **kwargs):
        super(TaggedDhcpServer, self).config(**kwargs)
        self.cmd('%s -q -4 -pf %s -cf %s %s' % (self.binFile, self.pidFile, self.configFile, self.vlanIntf))

        disable_offload(self, self.vlanIntf)

    def terminate(self, **kwargs):
        self.cmd('kill -9 `cat %s`' % self.pidFile)
        self.cmd('rm -rf %s' % self.pidFile)
        super(TaggedDhcpServer, self).terminate()

class DualHomedDhcpClient(Host):
    def __init__(self, name, *args, **kwargs):
        super(DualHomedDhcpClient, self).__init__(name, **kwargs)
        self.pidFile = '/run/dhclient-%s.pid' % self.name
        self.bond0 = None

    def config(self, **kwargs):
        super(DualHomedDhcpClient, self).config(**kwargs)
        intf0 = self.intfs[0].name
        intf1 = self.intfs[1].name
        self.bond0 = "%s-bond0" % self.name
        self.cmd('modprobe bonding')
        self.cmd('ip link add %s type bond miimon 100 mode balance-xor xmit_hash_policy layer2+3' % self.bond0)
        self.cmd('ip link set %s down' % intf0)
        self.cmd('ip link set %s down' % intf1)
        self.cmd('ip link set %s master %s' % (intf0, self.bond0))
        self.cmd('ip link set %s master %s' % (intf1, self.bond0))
        self.cmd('ip addr flush dev %s' % intf0)
        self.cmd('ip addr flush dev %s' % intf1)
        self.cmd('ip link set %s up' % self.bond0)
        self.cmd('dhclient -q -4 -nw -pf %s %s' % (self.pidFile, self.bond0))

        disable_offload(self, self.bond0)

    def terminate(self, **kwargs):
        self.cmd('ip link set %s down' % self.bond0)
        self.cmd('ip link delete %s' % self.bond0)
        self.cmd('kill -9 `cat %s`' % self.pidFile)
        self.cmd('rm -rf %s' % self.pidFile)
        super(DualHomedDhcpClient, self).terminate()

# Dual-homed Client that has both IPv4 and IPv6 addresses
class DualHomedDhcp4and6Client(Host):
    def __init__(self, name, *args, **kwargs):
        super(DualHomedDhcp4and6Client, self).__init__(name, **kwargs)
        self.pidFile4 = '/run/dhclient-%s-4.pid' % self.name
        self.pidFile6 = '/run/dhclient-%s-6.pid' % self.name
        self.bond0 = None

    def config(self, **kwargs):
        super(DualHomedDhcp4and6Client, self).config(**kwargs)
        intf0 = self.intfs[0].name
        intf1 = self.intfs[1].name
        self.bond0 = "%s-bond0" % self.name
        self.cmd('modprobe bonding')
        self.cmd('ip link add %s type bond miimon 100 mode balance-xor xmit_hash_policy layer2+3' % self.bond0)
        self.cmd('ip link set %s down' % intf0)
        self.cmd('ip link set %s down' % intf1)
        self.cmd('ip link set %s master %s' % (intf0, self.bond0))
        self.cmd('ip link set %s master %s' % (intf1, self.bond0))
        self.cmd('ip -4 addr flush dev %s' % intf0)
        self.cmd('ip -4 addr flush dev %s' % intf1)
        self.cmd('ip addr flush dev %s' % intf0)
        self.cmd('ip addr flush dev %s' % intf1)
        time.sleep(3)
        self.cmd('ip link set %s up' % self.bond0)
        self.cmd('dhclient -q -4 -nw -pf %s %s' % (self.pidFile4, self.bond0))
        self.cmd('dhclient -q -6 -nw -pf %s %s' % (self.pidFile6, self.bond0))

        disable_offload(self, self.bond0)

    def terminate(self, **kwargs):
        self.cmd('ip link set %s down' % self.bond0)
        self.cmd('ip link delete %s' % self.bond0)
        self.cmd('kill -9 `cat %s`' % self.pidFile4)
        self.cmd('kill -9 `cat %s`' % self.pidFile6)
        self.cmd('rm -rf %s' % self.pidFile4)
        self.cmd('rm -rf %s' % self.pidFile6)
        super(DualHomedDhcp4and6Client, self).terminate()

# Utility for IPv6
def mac_to_ipv6_linklocal(mac):
    '''
    Convert mac address to link-local IPv6 address
    '''
    # Remove the most common delimiters; dots, dashes, etc.
    mac_value = int(mac.translate(None, ' .:-'), 16)

    # Split out the bytes that slot into the IPv6 address
    # XOR the most significant byte with 0x02, inverting the
    # Universal / Local bit
    high2 = mac_value >> 32 & 0xffff ^ 0x0200
    high1 = mac_value >> 24 & 0xff
    low1 = mac_value >> 16 & 0xff
    low2 = mac_value & 0xffff

    return 'fe80::{:04x}:{:02x}ff:fe{:02x}:{:04x}'.format(high2, high1, low1, low2)

# Parses Trellis parameters
def parse_trellis_args():
    parser = argparse.ArgumentParser(description="Trellis Arguments")
    parser.add_argument("-c", "--controllers", help = "Comma Separated List of ONOS controllers",
                        required = True, default = "")
    return parser.parse_args()

# Gets a mininet instance
def get_mininet(arguments, topo, switch):
    net = Mininet(topo=topo, controller=None, switch=switch)

    if arguments.controllers:
        controllers = arguments.controllers.split(',')
        controller_number = 0
        for controller in controllers:
            net.addController(RemoteController('c' + str(controller_number), ip=controller))
            controller_number += 1
    return net

# Generates the Zebra config files
def set_up_zebra_config(controllers_string):
    zebra_config = "log file /var/log/quagga/zebradbgp{}.log\n" \
                   "hostname zebra-bgp{}\n" \
                   "password quagga\n" \
                    "!\n" \
                    "! Default route via virtual management switch\n" \
                    "!\n" \
                    "ip route 0.0.0.0/0 172.16.0.1\n" \
                    "!\n" \
                    "fpm connection ip {} port 2620\n"
    controllers = controllers_string.split(',')

    controller1 = controllers[0]
    if (len(controllers) > 1):
        controller2 = controllers[1]
    else:
        controller2 = controller1


    zebra1 = zebra_config.format("1", "1", controller1)
    zebra2 = zebra_config.format("2", "2", controller2)

    with open("zebradbgp1.conf", "w") as config_file_1:
        config_file_1.write(zebra1)

    with open("zebradbgp2.conf", "w") as config_file_2:
        config_file_2.write(zebra2)

# Disable NIC offloading
def disable_offload(host, intf):
    for attr in ["rx", "tx", "sg"]:
        cmd = "/sbin/ethtool --offload %s %s off" % (intf, attr)
        host.cmd(cmd)

