#!/usr/bin/python

"""
Libraries for Trellis hosts.
"""

import sys
sys.path.append('..')
from mininet.node import Host
from routinglib import RoutedHost

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

    def terminate(self, **kwargs):
        self.cmd('ip link remove link %s' % self.vlanIntf)
        super(TaggedRoutedHost, self).terminate()

class DhcpClient(Host):
    def __init__(self, name, *args, **kwargs):
        super(DhcpClient, self).__init__(name, **kwargs)
        self.pidFile = '/run/dhclient-%s.pid' % self.name

    def config(self, **kwargs):
        super(DhcpClient, self).config(**kwargs)
        self.cmd('ip addr flush dev %s' % self.defaultIntf())
        self.cmd('dhclient -q -4 -nw -pf %s %s' % (self.pidFile, self.defaultIntf()))

    def terminate(self, **kwargs):
        self.cmd('kill -9 `cat %s`' % self.pidFile)
        self.cmd('rm -rf %s' % self.pidFile)
        super(DhcpClient, self).terminate()

class DhcpServer(RoutedHost):
    binFile = '/usr/sbin/dhcpd'
    pidFile = '/run/dhcp-server/dhcpd.pid'
    configFile = './dhcpd.conf'

    def config(self, **kwargs):
        super(DhcpServer, self).config(**kwargs)
        self.cmd('%s -q -4 -pf %s -cf %s %s' % (self.binFile, self.pidFile, self.configFile, self.defaultIntf()))

    def terminate(self, **kwargs):
        self.cmd('kill -9 `cat %s`' % self.pidFile)
        self.cmd('rm -rf %s' % self.pidFile)
        super(DhcpServer, self).terminate()

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
        self.cmd('ip link add %s type bond' % self.bond0)
        self.cmd('ip link set %s down' % intf0)
        self.cmd('ip link set %s down' % intf1)
        self.cmd('ip link set %s master %s' % (intf0, self.bond0))
        self.cmd('ip link set %s master %s' % (intf1, self.bond0))
        self.cmd('ip addr flush dev %s' % intf0)
        self.cmd('ip addr flush dev %s' % intf1)
        self.cmd('ip link set %s up' % self.bond0)
        self.cmd('dhclient -q -4 -nw -pf %s %s' % (self.pidFile, self.bond0))

    def terminate(self, **kwargs):
        self.cmd('ip link set %s down' % self.bond0)
        self.cmd('ip link delete %s' % self.bond0)
        self.cmd('kill -9 `cat %s`' % self.pidFile)
        self.cmd('rm -rf %s' % self.pidFile)
        super(DualHomedDhcpClient, self).terminate()
