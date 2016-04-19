#!/usr/bin/python

from mininet.topo import Topo
from mininet.net import Mininet
from mininet.cli import CLI
from mininet.log import setLogLevel, info
from mininet.node import RemoteController, OVSSwitch
from routinglib import BgpRouter

class BgpRouterDeployTopo( Topo ):
    "Sets up control plane components for BgpRouter deployment"
    
    def __init__( self, *args, **kwargs ):
        Topo.__init__( self, *args, **kwargs )
        s1 = self.addSwitch('s1', dpid='0000000000000001')

        sdnAs = 65000

        # Set up BGP speakers
        bgp1eth0 = { 'ipAddrs' : ['1.1.1.11/24'] }

        bgp1eth1 = [
            { 'vlan': 1,
              'mac':'00:00:00:00:00:01', 
              'ipAddrs' : ['192.168.10.101/24'] },
            { 'vlan': 2,
              'mac':'00:00:00:00:00:02', 
              'ipAddrs' : ['192.168.20.101/24'] }
        ]

        bgp1Intfs = { 'bgp1-eth0' : bgp1eth0,
                      'bgp1-eth1' : bgp1eth1 }

        neighbors = [{'address':'192.168.10.1', 'as':65001},
                     {'address':'192.168.20.1', 'as':65001},
                     {'address':'192.168.30.1', 'as':65002},
                     {'address':'192.168.40.1', 'as':65003},
                     {'address':'1.1.1.1', 'as':sdnAs, 'port': 2000}]
        
        bgp1 = self.addHost( "bgp1", interfaces=bgp1Intfs, asNum=sdnAs, 
                             neighbors=neighbors, routes=[], cls=BgpRouter)
        
        root = self.addHost('root', ip='1.1.1.1/24', inNamespace=False)

        self.addLink( bgp1, root )
        self.addLink( bgp1, s1 )

if __name__ == "__main__":
    setLogLevel('debug')
    topo = BgpRouterDeployTopo()

    net = Mininet(topo=topo, controller=RemoteController, switch=OVSSwitch)

    net.start()

    CLI(net)

    net.stop()

    info("done\n")
