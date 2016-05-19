#!/usr/bin/python

from mininet.topo import Topo
from mininet.net import Mininet
from mininet.cli import CLI
from mininet.log import setLogLevel
from mininet.node import RemoteController, OVSSwitch, UserSwitch
from mininet.nodelib import NAT
from routinglib import QuaggaRouter
from routinglib import BgpProtocol, OspfProtocol
from routinglib import RoutedNetwork, RoutedHost, Router
from ipaddress import ip_network
from routinglib import PimProtocol

#onosIps = ['192.168.56.11']

cordOnos = '192.168.56.12'
fabricOnos = '192.168.56.11'

c0 = RemoteController( 'c0', ip=fabricOnos )
c1 = RemoteController( 'c1', ip=cordOnos )

cmap = { 's1': c0, 's2': c1 }

class MultiSwitch( UserSwitch ):
        "Custom Switch() subclass that connects to different controllers"
        def start( self, controllers ):
            return UserSwitch.start( self, [ cmap[ self.name ] ] )

class MulticastTopo( Topo ):
    """Topology for testing multicast in CORD.
       Contains two switches:
         (1) stand-in for the OLT, where the IGMP snooping will happen
         (2) vRouter/fabric leaf where the PIM to upstream happens"""
    
    def __init__( self, *args, **kwargs ):
        Topo.__init__( self, *args, **kwargs )
        
        QuaggaRouter.binDir='/home/jono/shared/quagga/build/bin'
        
        # vRouter switch
        s1 = self.addSwitch('s1', dpid='1')
        # IGMP switch
        s2 = self.addSwitch('s2', dpid='2')
        
        eth0 = { 'ipAddrs' : ['10.0.3.1/24'] }
        eth1 = { 'ipAddrs' : ['10.0.2.254/24']}
        intfs = {'r1-eth0' : eth0,
                 'r1-eth1' : eth1}
        
        pim = PimProtocol(configFile='configs/pim.conf')
        #bgp = BgpProtocol(asNum=65001, neighbors=[{'address' : '10.0.3.2', 'as' : 65000}], routes=['10.0.2.0/24'])
        ospf = OspfProtocol()
        r1 = self.addHost('r1', interfaces=intfs, cls=QuaggaRouter,
                          protocols=[pim, ospf])
        
        self.addLink(r1, s1)
        
        RoutedNetwork.build(self, r1, 'h1', [ip_network(u'10.0.2.0/24')])
        
        
        cpintfs = {'cp1-eth0' : { 'mac' : '00:00:00:00:00:01', 'ipAddrs' : ['10.0.3.2/24', '10.0.1.100/24'] },
                   'cp1-eth1' : { 'ipAddrs' : ['1.1.1.1/24']} }
        #bgp = BgpProtocol(asNum=65000, neighbors=[{'address' : '10.0.3.1', 'as': 65001}])
        ospf = OspfProtocol()
        cp1 = self.addHost('cp1', cls=QuaggaRouter, interfaces=cpintfs, protocols=[ospf],
                           fpm=fabricOnos, defaultRoute='1.1.1.254')
        #cp1 = self.addHost('cp1', cls=Router, ips=['10.0.3.2/24'], mac='00:00:00:00:00:01')
        
        nat = self.addHost('nat', cls=NAT, 
                                   ip='1.1.1.254/24', 
                                   subnet='1.1.1.0/24', inNamespace=False);
        self.addLink(cp1, s1)
        self.addLink(cp1, nat)
        
        h2 = self.addHost('h2', ip="10.0.1.1/24", defaultRoute="via 10.0.1.254", mac="00:00:00:00:00:02", inNamespace=True)
        self.addLink(h2, s2)
        self.addLink(s2, s1)

if __name__ == "__main__":
    setLogLevel('debug')
    topo = MulticastTopo()

    net = Mininet(topo=topo, switch=MultiSwitch, controller=None)
    
    net.addController(c0)
    net.addController(c1)

    h2 = net.get('h2')
    h2.cmd('ethtool --offload h2-eth0 tx off')
    r1 = net.get('r1')
    r1.cmd('ethtool --offload r1-eth0 tx off')
    cp1 = net.get('cp1')
    cp1.cmd('ethtool --offload cp1-eth0 tx off')

    net.start()

    CLI(net)

    net.stop()
