#!/usr/bin/python

from mininet.topo import Topo
from mininet.net import Mininet
from mininet.node import RemoteController
from mininet.cli import CLI
from mininet.log import setLogLevel, info
from mininet.node import OVSBridge
from routinglib import BgpRouter, RoutedHost
from onoslib import ONOSHostSdnipCluster

onoses = [ '192.168.56.11', '192.168.56.12' ]

class BgpRouterDeployTopo( Topo ):
    "Our familiar ONS demo topology"
    
    def __init__( self, *args, **kwargs ):
        Topo.__init__( self, *args, **kwargs )
        sw1 = self.addSwitch('sw1', dpid='00000000000000a1')
        sw2 = self.addSwitch('sw2', dpid='00000000000000a2')
        sw3 = self.addSwitch('sw3', dpid='00000000000000a3')
        sw4 = self.addSwitch('sw4', dpid='00000000000000a4')
        sw5 = self.addSwitch('sw5', dpid='00000000000000a5')
        sw6 = self.addSwitch('sw6', dpid='00000000000000a6')
        
        #Note this switch isn't part of the SDN topology
        as6sw = self.addSwitch('as6sw', dpid='00000000000000a7', cls=OVSBridge)

        #AS2 host
        host3eth0 = { 'mac':'00:00:00:00:02:01', 'ipAddrs' : [ '192.168.10.1/24' ] }
        host3eth1 = { 'mac':'00:00:00:00:02:02', 'ipAddrs' : [ '192.168.20.1/24' ] }
        host3eth2 = { 'ipAddrs' : [ '172.16.20.254/24' ] }
        host3Intfs = {'host3-eth0' : host3eth0,
                      'host3-eth1' : host3eth1,
                      'host3-eth2' : host3eth2 }
        host3neigh = [{'address':'192.168.10.101', 'as':64513},
                      {'address':'192.168.20.101', 'as':64513}]
        host3routes = ['127.16.10.0/24']
        
        host3 = self.addHost( 'host3', interfaces=host3Intfs, asNum=65001, 
                              neighbors=host3neigh, routes=host3routes, 
                              cls=BgpRouter)
        
        as2host = self.addHost( 'as2host', cls=RoutedHost, ip='172.16.20.1/24', 
                                route='172.16.20.254' )


        #AS3 host
        host4eth0 = { 'mac':'00:00:00:00:03:01', 'ipAddrs' : [ '192.168.30.1/24' ] }
        host4eth1 = { 'ipAddrs' : [ '172.16.30.254/24' ] }
        host4Intfs = {'host4-eth0' : host4eth0,
                      'host4-eth1' : host4eth1 }
        host4neigh = [{'address':'192.168.30.101', 'as':64513}]
        host4routes = ['172.16.30.0/24']
        host4 = self.addHost( 'host4', interfaces=host4Intfs, asNum=65002, 
                              neighbors=host4neigh, routes=host4routes,
                              cls=BgpRouter)
 
        as3host = self.addHost( 'as3host', cls=RoutedHost, ip='172.16.30.1/24', 
                                route='172.16.30.254' )


        #AS4 host
        host5eth0 = { 'mac':'00:00:00:00:04:01', 'ipAddrs' : [ '192.168.40.1/24' ] }
        host5eth1 = { 'ipAddrs' : [ '172.16.40.254/24' ] }
        host5Intfs = {'host5-eth0' : host5eth0,
                      'host5-eth1' : host5eth1 }
        host5neigh = [{'address':'192.168.40.101', 'as':64513}]
        host5routes = ['172.16.40.0/24']
        host5 = self.addHost( 'host5', interfaces=host5Intfs, asNum=65003, 
                              neighbors=host5neigh, routes=host5routes,
                              cls=BgpRouter)

        as4host = self.addHost( 'as4host', cls=RoutedHost, ip='172.16.40.1/24', 
                                route='172.16.40.254' )
        
        #AS6 host
        #as6rs = self.addHost( 'as6rs' )
        #as6rs2 = self.addHost( 'as6rs2' )
        #as6router = self.addHost( 'as6router' )
        #as6host = self.addHost( 'as6host' )

        # Create a control network
        onosCluster = ONOSHostSdnipCluster(controlSubnet='192.168.50.0/24',
                                           dataSubnet='1.1.1.0/24', numInstances=2)
        cs1 = onosCluster.create(self)
        #cs0 = self.createControlNet((u'192.168.50.0/24'), (u'1.1.1.0/24'), numOnos=2)

        # Set up BGP speakers
        bgp1eth0 = { 'ipAddrs' : ['1.1.1.11/24'] }
        bgp1eth1 = { 'mac':'00:00:00:00:00:01', 
                    'ipAddrs' : ['192.168.10.101/24',
                                 '192.168.20.101/24',
                                 '192.168.30.101/24',
                                 '192.168.40.101/24',] }
        bgp1Intfs = { 'BGP1-eth0' : bgp1eth0,
                     'BGP1-eth1' : bgp1eth1 }
        bgp1neigh = [{'address':'192.168.10.1', 'as':65001},
                     {'address':'192.168.20.1', 'as':65001},
                     {'address':'192.168.30.1', 'as':65002},
                     {'address':'192.168.40.1', 'as':65003},
                     {'address':'1.1.1.1', 'as':64513},
                     {'address':'1.1.1.2', 'as':64513},
                     {'address':'1.1.1.12', 'as':64513}]
        
        bgp1 = self.addHost( "BGP1", interfaces=bgp1Intfs, asNum=64513, 
                             neighbors=bgp1neigh, routes=[], cls=BgpRouter)
        
        self.addLink( bgp1, cs1 )
        self.addLink( bgp1, sw1 )
        
        #bgp2eth0 = { 'ipAddrs' : ['1.1.1.12/24'] }
        #bgp2eth1 = { 'mac':'00:00:00:00:00:02', 
        #            'ipAddrs' : ['192.168.10.102/24',
        #                         '192.168.20.102/24',
        #                         '192.168.30.102/24',
        #                         '192.168.40.102/24',] }
        #bgp2Intfs = { 'BGP2-eth0' : bgp2eth0,
        #             'BGP2-eth1' : bgp2eth1 }
        
        #bgp2 = self.addHost( "BGP2", cls=BgpRouter, 
        #                        quaggaConfFile = '../onsdemo/quagga-sdn2.conf', 
        #                        zebraConfFile = zebraConf, 
        #                        interfaces=bgp2Intfs )
        
        #self.addLink( bgp2, cs0 )
        #self.addLink( bgp2, sw4 )
        
        #Links to the multihomed AS
        self.addLink( host3, sw3 )
        self.addLink( host3, sw5 )
        self.addLink( as2host, host3 )
        #Single links to the remaining two ASes
        self.addLink( host4, sw2 )
        self.addLink( as3host, host4 )
        self.addLink( host5, sw6 )
        self.addLink( as4host, host5 )
        #AS3-AS4 link
        #self.addLink( host4, host5)
        #Add new AS6 to its bridge
        #self.addLink( as6rs, as6sw )
        #self.addLink( as6rs2, as6sw )
        #self.addLink( as6router, as6sw )
        #self.addLink( as6host, as6router )
        #for i in range(1, 10):
        #    host = self.addHost('as6host%d' % i)
        #    self.addLink(host, as6router)

        self.addLink( sw1, sw2 )
        self.addLink( sw1, sw3 )
        self.addLink( sw2, sw4 )
        self.addLink( sw3, sw4 )
        self.addLink( sw3, sw5 )
        self.addLink( sw4, sw6 )
        self.addLink( sw5, sw6 )
        self.addLink( as6sw, sw4 )

if __name__ == "__main__":
    setLogLevel('debug')
    topo = BgpRouterDeployTopo()

    net = Mininet(topo=topo, controller=None)
    for i in range(len(onoses)):
        net.addController( RemoteController( 'c%s' % (i+1), ip=onoses[i], checkListening=False )  )

    net.start()

    CLI(net)

    net.stop()

    info("done\n")
