#!/usr/bin/python

from mininet.topo import Topo
from mininet.net import Mininet
from mininet.node import RemoteController, OVSBridge
from mininet.cli import CLI
from mininet.log import setLogLevel, info
from routinglib import BasicAutonomousSystem, RouteServerAutonomousSystem
from routinglib import SdnAutonomousSystem, AutonomousSystem
from ipaddress import ip_network

onoses = [ '192.168.56.11' ]

class SdnTopo( Topo ):
    "Topology built using higher-level abstractions (ASes)"
    
    def __init__( self, *args, **kwargs ):
        Topo.__init__( self, *args, **kwargs )
        sw1 = self.addSwitch('sw1', dpid='00000000000000a1')
        sw2 = self.addSwitch('sw2', dpid='00000000000000a2')
        sw3 = self.addSwitch('sw3', dpid='00000000000000a3')
        sw4 = self.addSwitch('sw4', dpid='00000000000000a4')
        sw5 = self.addSwitch('sw5', dpid='00000000000000a5')
        sw6 = self.addSwitch('sw6', dpid='00000000000000a6')
        
        # SDN AS
        sdnAs = SdnAutonomousSystem(onoses, numBgpSpeakers=1, asNum=65000)
        
        # Normal ASes
        as1 = BasicAutonomousSystem(1, [ip_network(u'172.16.10.0/24')])

        AutonomousSystem.addPeering(as1, sdnAs)
        as1.addLink(sw3)
        as1.build(self)

        as2 = BasicAutonomousSystem(2, [ip_network(u'172.16.20.0/24')])
        
        AutonomousSystem.addPeering(as2, sdnAs)
        as2.addLink(sw2)
        as2.build(self)
        
        as3 = BasicAutonomousSystem(3, [ip_network(u'172.16.30.0/24')])
        
        AutonomousSystem.addPeering(as3, sdnAs)
        as3.addLink(sw6)
        as3.build(self)

        # AS containing a route server
        #as4 = RouteServerAutonomousSystem('192.168.60.2/24', 4, '192.168.60.1/24', 
        #                                  [ip_network(u'172.16.60.0/24')])
        #as4.build(self, sw4);
        
        cs0 = self.addSwitch('cs0', cls=OVSBridge)
        
        sdnAs.build(self, sw1, cs0)

        self.addLink( sw1, sw2 )
        self.addLink( sw1, sw3 )
        self.addLink( sw2, sw4 )
        self.addLink( sw3, sw4 )
        self.addLink( sw3, sw5 )
        self.addLink( sw4, sw6 )
        self.addLink( sw5, sw6 )

if __name__ == "__main__":
    setLogLevel('debug')
    topo = SdnTopo()

    net = Mininet(topo=topo, controller=None)
    for i in range(len(onoses)):
        net.addController( RemoteController( 'c%s' % (i+1), ip=onoses[i], checkListening=False )  )

    net.start()

    CLI(net)

    net.stop()

    info("done\n")
