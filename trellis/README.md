Trellis Leaf-Spine Fabric
=========================

# Introduction
This folder contains Mininet scripts and corresponding config files that
can be used to emulate Trellis leaf-spine fabric, vRouter and DHCP relay.
Current Mininet setup only works with ONOS 1.12 and above. We recommend you use the tip of 1.12 branch.

# Download
`git clone https://gerrit.onosproject.org/routing`

# Manual Installation

## Ubuntu 16.04 LTS
Some dependencies need to be installed for a fresh Ubuntu.
```
sudo apt-get update
sudo apt-get install -y gawk texinfo python-pip build-essential iptables automake autoconf libtool
sudo pip install -U pip
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

In order to start the quagga related daemons, you should create a user `quagga`
and set the correct read/write permission to local state directory(`--localstatedir`)
and configuration directory(`--sysconfdir`).

```
git clone -b onos-1.11 https://gerrit.opencord.org/quagga
cd quagga
./bootstrap.sh
./configure --enable-fpm --sbindir=/usr/lib/quagga enable_user=root enable_group=root
make
sudo make install
cd ..
sudo ldconfig
```

## ONOS - Installation
Learn about how to setup ONOS at: https://wiki.onosproject.org/.
After installation, the following ONOS apps need to be activated.

`export ONOS_APPS=drivers,openflow,segmentrouting,fpm,dhcprelay,netcfghostprovider,routeradvertisement,mcast`

## ONOS - Network Config
`onos-netcfg <onos-ip> routing/trellis/trellis.json`

## Disable/Modify AppArmor
The apparmor will set dhcpd in enforce mode. We will need to disable the profile.
```
sudo ln -s /etc/apparmor.d/usr.sbin.dhcpd /etc/apparmor.d/disable/
sudo apparmor_parser -R /etc/apparmor.d/usr.sbin.dhcpd
```

The apparmor rules of dhclient will restrict the dhclient to write files to directory /var/lib/.
We need to modify the rules of dhclient profile and restart the apparmor.
```
sudo /etc/init.d/apparmor stop
sudo sed -i '30i  /var/lib/dhcp{,3}/dhcpclient* lrw,' /etc/apparmor.d/sbin.dhclient
sudo /etc/init.d/apparmor start
```

## Start Mininet Emulation
```
cd routing/trellis
sudo ./trellis.py --controllers ONOS_CONTROLLER_IP1,ONOS_CONTROLLER_IP2,...,ONOS_CONTROLLER_IPN
```

## Verify Network Connectivity
In Mininet, run
- `h1 ping 10.0.99.2` to check IPv4 connectivity
- `h1v6 ping6 2000::9902` to check IPv6 connectivity

# Vagrant
We also provide a mininet VM image supported by Vagrant file.
In that VM environment, you only need to modify the IP address of ONOS controller for
`trellis.py` and `zebradbgp*.conf`.

In order to use the Vagrant, make sure you have already installed the Vagrant in your environment.

## Start the VM
```
vagrant up
```

## Start the ONOS
Start the ONOS controller and set the config via `onos-netcfg` on the other host.

## Operate the VM
Type the following command to ssh into the VM environment.
```
vagrant ssh
```

Now start mininet to test
```
cd routing/trellis
sudo ./trellis.py --controllers ONOS_CONTROLLER_IP1,ONOS_CONTROLLER_IP2,...,ONOS_CONTROLLER_IPN
```

# Troubleshooting
- Services in the emulated hosts may still be alive if Mininet is not terminated properly.
In that case, simply run the following command to clean up.
```
sudo killall -9 dhclient dhcpd zebra bgpd
sudo mn -c
```
