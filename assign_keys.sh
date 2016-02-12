#!/bin/bash

#set -x

VZ6_BASE_IP=172.3.0.3
KVM_BASE_IP=172.0.0.3

PASS="1q2w3e"

DEFAULT_NUM=36
NUM=${1:-DEFAULT_NUM}

assign_ips()
{
	BASE_IP=$1
	bip=$(echo ${BASE_IP} | cut -d. -f4)
	for i in $(seq ${bip} $((bip + NUM * 4 - 1))); do
	        IP="$(echo ${BASE_IP} | cut -d. -f1-3).$i"
		echo $IP
		expect -c "
			spawn ssh root@$IP mkdir -p .ssh
			expect -nocase \"password: \" {send \"$PASS\n\"; interact}"

		expect -c "
			spawn scp /root/.ssh/authorized_keys root@$IP:/root/.ssh/
			expect -nocase \"password: \" {send \"$PASS\n\"; interact}"
	done
}

assign_ips $VZ6_BASE_IP
#assign_ips $KVM_BASE_IP

