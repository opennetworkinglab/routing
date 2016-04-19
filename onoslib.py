"""
Libraries for using ONOS from within Mininet.
"""

from mininet.node import OVSBridge
from mininet.util import netParse, ipStr
import os, sys, imp

# Import the ONOS classes from onos.py in the ONOS repository
if not 'ONOS_ROOT' in os.environ:
    print 'ONOS_ROOT is not set.'
    print 'Try running the script with \'sudo -E\' to pass your environment in.'
    sys.exit(1)

onos_path = os.path.join(os.path.abspath(os.environ['ONOS_ROOT']), 'tools/test/topos/onos.py')
onos = imp.load_source('onos', onos_path)
from onos import ONOS

class ONOSHostCluster(object):
    def __init__(self, controlSubnet='192.168.1.0/24', numInstances=1, basename='ONOS',
                 features=[]):
        self.controlSubnet = controlSubnet
        self.numInstances = numInstances
        self.basename = basename
        self.instances = []
        self.features = features
        
    def create(self, topology):
        cs0 = topology.addSwitch('cs0', cls=OVSBridge)
        
        ctrlIp, ctrlPrefixLen = netParse(self.controlSubnet)
        
        for i in range(1, self.numInstances + 1):
            strCtrlIp = '%s/%i' % (ipStr(ctrlIp + i), ctrlPrefixLen)

            c = topology.addHost('%s%s' % (self.basename, i), cls=ONOS, inNamespace=True,
                              ip=strCtrlIp,
                              features=['onos-app-config', 'onos-app-proxyarp',
                                        'onos-core'] + self.features,
                              reactive=False)
            
            topology.addLink(c, cs0, params1={ 'ip' : strCtrlIp })
            
            self.instances.append(c)
            
        # Connect switch to root namespace so that data network
        # switches will be able to talk to us
        highestIp = '%s/%i' % (ipStr(ctrlIp + (2 ** (32 - ctrlPrefixLen)) - 2), ctrlPrefixLen)
        root = topology.addHost('root', inNamespace=False, ip=highestIp)
        topology.addLink(root, cs0)
        
class ONOSHostSdnipCluster(ONOSHostCluster):
    
    def __init__(self, dataSubnet='10.0.0.0/24', features=['onos-app-sdnip'], **kwargs):
        super(ONOSHostSdnipCluster, self).__init__(features=features, **kwargs)

        self.dataSubnet = dataSubnet
        
    def create(self, topology):
        super(ONOSHostSdnipCluster, self).create(topology)
        
        cs1 = topology.addSwitch('cs1', cls=OVSBridge)
        
        dataIp, dataPrefixLen = netParse(self.dataSubnet)
        for i in range(1, len(self.instances) + 1):
            c = self.instances[i-1]
            strDataIp = '%s/%i' % (ipStr(dataIp + i), dataPrefixLen)
            topology.addLink(c, cs1, params1={ 'ip' : strDataIp })
            
        return cs1