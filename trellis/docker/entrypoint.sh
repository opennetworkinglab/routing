#!/bin/bash

# Select topology to emulate
TOPO=${TOPO:-trellis}
ONOS_HOST=${ONOS_HOST:-localhost}

# Resolve ONOS IP
ONOS_IP=`getent hosts $ONOS_HOSTNAME | awk '{ print $1 }'`

# Start and configure OVS
# Avoid using Linux service since it will attempt but fail the kernel module check
/usr/share/openvswitch/scripts/ovs-ctl --no-ovs-vswitchd --no-monitor --system-id=random start
/usr/sbin/ovs-vswitchd --detach
ovs-vsctl set Open_vSwitch . other_config:vlan-limit=2

# Push netcfg to ONOS
cd routing/trellis
echo ${ONOS_IP}
head ${TOPO}.json
onos-netcfg ${ONOS_IP} ${TOPO}.json

# Start mininet
./${TOPO}.py -c ${ONOS_IP}
