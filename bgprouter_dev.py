#!/usr/bin/python

from mininet.topo import Topo
from mininet.net import Mininet
from mininet.cli import CLI
from mininet.log import setLogLevel, info
from mininet.node import RemoteController, OVSBridge
from routinglib import BasicAutonomousSystem
from routinglib import SdnAutonomousSystem, AutonomousSystem
from routinglib import generateRoutes


class BgpRouterTopo( Topo ):
    "Single switch topology for testing the BgpRouter"
    
    def __init__( self, *args, **kwargs ):
        Topo.__init__( self, *args, **kwargs )
        # Router switch
        s1 = self.addSwitch('s1', dpid='00000000000000a1')
        
        # Control plane switch for BGP daemon
        s7 = self.addSwitch('s7', dpid='00000000000000a7')
        
        # SDN AS
        onosIps = ['192.168.56.11']
        sdnAs = SdnAutonomousSystem(onosIps, numBgpSpeakers=1, asNum=65000)
        
        numRoutesPerAs = 1
        
        # Normal ASes
        as1 = BasicAutonomousSystem(1, 
                    generateRoutes(u'10.1.0.0/16', numRoutesPerAs))
        AutonomousSystem.addPeering(as1, sdnAs, useVlans=True)
        as1.addLink(s1)
        as1.build(self)

        as2 = BasicAutonomousSystem(2, 
                    generateRoutes(u'10.2.0.0/16', numRoutesPerAs))
        AutonomousSystem.addPeering(as2, sdnAs, useVlans=True)
        as2.addLink(s1)
        as2.build(self)
        
        as3 = BasicAutonomousSystem(3, 
                    generateRoutes(u'10.3.0.0/16', numRoutesPerAs))
        AutonomousSystem.addPeering(as3, sdnAs, useVlans=True)
        as3.addLink(s1)
        as3.build(self)
        
        as4 = BasicAutonomousSystem(4, 
                    generateRoutes(u'10.4.0.0/16', numRoutesPerAs))
        AutonomousSystem.addPeering(as4, sdnAs, useVlans=False)
        as4.addLink(s1)
        as4.build(self)
        
        # SDN AS (internal BGP speaker) connects to control plane switch
        cs0 = self.addSwitch('cs0', cls=OVSBridge)
        sdnAs.build(self, s7, cs0)

if __name__ == "__main__":
    setLogLevel('debug')
    topo = BgpRouterTopo()

    net = Mininet(topo=topo, controller=None)
    net.addController(RemoteController('c0', ip='192.168.56.11'))

    net.start()

    CLI(net)

    net.stop()

    info("done\n")
