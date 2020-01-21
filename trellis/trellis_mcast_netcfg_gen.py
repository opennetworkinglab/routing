#! /usr/bin/python

import json

# It contains the fixed parts of the netcfg.
# In this case, they are the ports of the leafs
# hosts attached to the leafs. These are parts
# that at the moment we don't need to scale
netcfg = {}

# Base latitude and longitude for access devices
groups_cord = {
  "0" : [36, -106],
  "1" : [36, -110],
  "2" : [36, -114],
  "3" : [36, -118]
}

# Groups, host per groups and networks for each access device
groups = 4
hosts_per_group = 48
networks = (("10.100.1.254/24", "2002::1ff/120", 100, 200), \
  ("10.100.2.254/24", "2002::2ff/120", 101, 201), \
  ("10.100.3.254/24", "2002::3ff/120", 102, 202), \
  ("10.100.4.254/24", "2002::4ff/120", 103, 203), )

def generateDpid(device):
  dpid = hex( int( device ) )[ 2: ]
  return '0' * ( 16 - len( dpid ) ) + dpid

# Generate ports config
def generate_port_cfg(host, device, networks):
  device_index = device + 1
  port_index = host + 1
  dpid = generateDpid(device_index)
  dpid_port = 'of:%s/%s' %(dpid, port_index)
  netcfg['ports'][dpid_port] = {}
  interfaces = []
  interface = {}
  ips = []
  network = ""
  vlan = ""
  if port_index % 2 == 0:
    network = networks[1]
    vlan = networks[3]
  else:
    network = networks[0]
    vlan = networks[2]
  ips.append(network)
  interface['ips'] = ips
  interface['vlan-untagged'] = vlan
  interfaces.append(interface)
  netcfg['ports'][dpid_port]["interfaces"] = interfaces

# Generate hosts coordinate
def generate_host_cfg(mac, index, layer, group, counter):
  lat = groups_cord[str(group)][0] - layer
  lon = index + groups_cord[str(group)][1]
  name = "%s%d" %("acc", counter + 1)
  data = {
    "basic" : {}
  }
  data["basic"]["name"] = name
  data["basic"]["latitude"] = float(lat)
  data["basic"]["longitude"] = float(lon)
  netcfg["hosts"]["%s/-1" % mac] = data

# Read initial netcfg from file
with open('trellis_mcast_netcfg_gen.json') as json_file:
    netcfg = json.load(json_file)

# Main function
counter = 0
for g in range(0, groups):
  index = 0
  layer = 0
  for h in range(0, hosts_per_group):
    mac = hex(counter + 1)[2:]
    mac = '0' * ( 12 - len( mac ) ) + mac
    mac = ':'.join(s.encode('hex') for s in mac.decode('hex'))
    index = counter % 3
    if index == 0 :
      layer = layer + 1
    generate_port_cfg(h, g, networks[g])
    generate_host_cfg(mac, index, layer, g, counter)
    counter = counter + 1

# Dump the netcfg on file
with open('data.txt', 'w') as outfile:
    json.dump(netcfg, outfile)

