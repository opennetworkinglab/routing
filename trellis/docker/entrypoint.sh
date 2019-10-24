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

cd routing/trellis
NETCFG=${EXTERNAL_VOLUME}/${NETCFG_FILE}
echo "Check custom config, ${NETCFG}"

# Use custom file if ${NETCFG_FILE} be set
if [[ ${NETCFG_FILE} ]]; then
    if [ -f ${NETCFG} ]; then
        echo "Detected custom cfg ${NETCFG}, use it"
        onos-netcfg ${ONOS_IP} ${NETCFG} || exit 0
    else
        echo "${NETCFG} does not exist"
        exit 0
    fi
fi

# Start mininet
./${TOPO}.py -c ${ONOS_IP}
