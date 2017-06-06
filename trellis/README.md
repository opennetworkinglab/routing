Trellis Leaf-Spine Fabric
=========================

# Introduction
This folder contains Mininet scripts and corresponding config files that
can be used to emulate Trellis leaf-spine fabric, vRouter and DHCP relay.

# Download
`git clone https://gerrit.onosproject.org/routing`

# Installation

## Ubuntu 16.04 LTS
Some dependencies need to be installed for a fresh Ubuntu.
```
sudo apt-get update
sudo apt-get install gawk texinfo python-pip
sudo pip install ipaddress
```

## Mininet
`sudo apt-get install mininet`

## OpenvSwitch
Mininet should install OVS for you.
Please run `sudo ovs-vsctl --version` and make sure the OVS version is above 2.5.0+.

## DHCP server
`sudo apt-get install isc-dhcp-server`

## Quagga
Trellis needs a special FPM patch for Quagga.

```
wget http://download.savannah.gnu.org/releases/quagga/quagga-0.99.23.tar.gz
wget https://wiki.opencord.org/download/attachments/1278529/fpm-remote.diff
tar -xzvf quagga-0.99.23.tar.gz
cd quagga-0.99.23
patch -p1 < ../fpm-remote.diff
./configure --enable-fpm --sbindir=/usr/lib
make
sudo make install
cd ..
```

## ONOS - Installation
Learn about how to setup ONOS at: https://wiki.onosproject.org/.
After installation, the following ONOS apps need to be activated.

`export ONOS_APPS=drivers,openflow,segmentrouting,fpm,dhcprelay,netcfghostprovider`

## ONOS - Network Config
`onos-netcfg <onos-ip> routing/trellis/trellis.json`


## Update Controller IP
The location of ONOS controller needs to be updated in several places, including
Mininet script and zebra config.

In `routing/trellis/trellis.py`
```
net.addController(RemoteController('c0', ip='192.168.56.11'))
net.addController(RemoteController('c1', ip='192.168.56.12'))
net.addController(RemoteController('c2', ip='192.168.56.13'))
```

In `routing/trellis/zebrabgp1.conf`
```
fpm connection ip 192.168.56.11 port 2620
```

## Start Mininet Emulation
```
cd routing/trellis
sudo ./trellis.py
```

## Verify Network Connectivity
In Mininet, run
- `h1 ping 10.0.99.2` to check IPv4 connectivity
- `h1v6 ping6 2000::9902` to check IPv6 connectivity

# Troubleshooting
- Services in the emulated hosts may still be alive if Mininet is not terminated properly.
In that case, simply run the following command to clean up.
```
sudo killall -9 dhclient dhcpd zebra bgpd
sudo mn -c
```
