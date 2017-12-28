	#modify ubuntu/xenial64 login password to ubuntu/ubuntu	
	(echo "ubuntu" ; sleep 1 ; echo "ubuntu")|sudo passwd ubuntu

	# install git apps
	sudo apt-get install git -y

	# Download source code
	git clone https://gerrit.onosproject.org/routing
	sed -i 's/setLogLevel('debug')/setLogLevel('info')/g' /home/ubuntu/routing/trellis

	# Ubuntu 16.04 LTS update
	sudo apt-get update
	sudo apt-get install -y gawk texinfo python-pip build-essential iptables automake autoconf libtool
	sudo pip install -U pip
	sleep 5
	sudo pip install -y ipaddress 

	# Install Mininet
	sudo apt-get install mininet -y
	# Install DHCP server
	sudo apt-get install isc-dhcp-server -y
	
	# Install Quagga
	git clone -b onos-1.11 https://gerrit.opencord.org/quagga
	cd quagga
	./bootstrap.sh
	./configure --enable-fpm --sbindir=/usr/lib/quagga
	make
	sudo make install
	cd ..

	# Install ONOS
	# ONOS Requirements installation
	sudo adduser sdn --system --group
	sudo apt-get install software-properties-common -y && \
	sudo add-apt-repository ppa:webupd8team/java -y && \
	sudo apt-get update && \
	echo "oracle-java8-installer shared/accepted-oracle-license-v1-1 select true" | sudo debconf-set-selections && \
	sudo apt-get install oracle-java8-installer oracle-java8-set-default -y
	sudo apt-get install curl
	export JAVA_HOME=/usr/lib/jvm/java-8-oracle	

	# ONOS installation
	cd /opt
	sudo wget -c http://downloads.onosproject.org/release/onos-1.12.0.tar.gz
	sudo tar xzf onos-1.12.0.tar.gz
	sudo mv onos-1.12.0 onos
	cd
	
	# Running ONOS as a service
	sudo cp /opt/onos/init/onos.initd /etc/init.d/onos
	sudo cp /opt/onos/init/onos.service /etc/systemd/system/
	sed -i 's/ONOS_APPS=${ONOS_APPS:-}/ONOS_APPS=openflow,segmentrouting,fpm,dhcprelay,netcfghostprovider,routeradvertisement/g' /opt/onos/bin/onos-service
	sudo service onos start
	sleep 20
	echo -e "20 sec \a \n"
	
	#ONOS Network Config	
	/opt/onos/bin/onos-netcfg 192.168.56.11 /home/ubuntu/routing/trellis/trellis.json
	
	sudo service onos stop	
	

	
	#Disable AppArmor
	sudo ln -s /etc/apparmor.d/usr.sbin.dhcpd /etc/apparmor.d/disable/
	sudo apparmor_parser -R /etc/apparmor.d/usr.sbin.dhcpd

	echo -e "****************** \a \n"
	sudo ovs-vsctl --version
	echo -e "****************** \a \n"
