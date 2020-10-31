FROM ubuntu:18.04
MAINTAINER Charles Chan <rascov@gmail.com>

ENV HOME /root

# Install dependencies
WORKDIR $HOME
RUN apt-get update && \
    DEBIAN_FRONTEND=noninteractive apt-get -yq --no-install-recommends install git gawk texinfo python-pip build-essential iptables automake autoconf libtool openvswitch-switch mininet \
    isc-dhcp-server isc-dhcp-client iputils-ping net-tools curl iproute2 ethtool && \
    pip install ipaddress && \
    rm -rf /var/lib/apt/lists/*

# Install Quagga
RUN git clone --depth 1 -b onos-1.11 https://gerrit.opencord.org/quagga
WORKDIR $HOME/quagga
RUN ./bootstrap.sh
RUN ./configure --enable-fpm --sbindir=/usr/lib/quagga enable_user=root enable_group=root
RUN make
RUN make install

# Clone Trellis simulation repo
WORKDIR $HOME
RUN git clone --depth 1 https://gerrit.onosproject.org/routing

# Update dynamic linker
RUN ldconfig

# Fetch ONOS netcfg tools
WORKDIR $HOME
RUN curl -o /usr/local/bin/onos-netcfg https://raw.githubusercontent.com/opennetworkinglab/onos/onos-1.12/tools/package/runtime/bin/onos-netcfg
RUN curl -o /usr/local/bin/_rest-port https://raw.githubusercontent.com/opennetworkinglab/onos/onos-1.12/tools/package/runtime/bin/_rest-port
RUN curl -o /usr/local/bin/_find-node https://raw.githubusercontent.com/opennetworkinglab/onos/onos-1.12/tools/package/runtime/bin/_find-node
RUN curl -o /usr/local/bin/_check-json https://raw.githubusercontent.com/opennetworkinglab/onos/onos-1.12/tools/package/runtime/bin/_check-json
RUN chmod a+x /usr/local/bin/onos-netcfg /usr/local/bin/_rest-port /usr/local/bin/_find-node /usr/local/bin/_check-json

# Copy useful Mininet utility
COPY m $HOME

# Copy start script
COPY entrypoint.sh $HOME

# Requirement for Mininet NAT class
RUN touch /etc/network/interfaces
