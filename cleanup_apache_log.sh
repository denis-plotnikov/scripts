#!/bin/bash
PATH=/usr/local/sbin:/usr/local/bin:/sbin:/bin:/usr/sbin:/usr/bin:
#set -x

THRESHOLD=50

VZ6_BASE_IP=172.3.0.3
KVM_BASE_IP=172.0.0.3

DEFAULT_NUM=36
NUM=${1:-DEFAULT_NUM}

LOG_FILE="/root/highload_demo/log_cleaner/clean.log"

clear_logs()
{
        BASE_IP=$1
        bip=$(echo ${BASE_IP} | cut -d. -f4)
        for i in $(seq ${bip} $((bip + NUM * 4 - 1))); do
                IP="$(echo ${BASE_IP} | cut -d. -f1-3).$i"
		DISK_USED=$(ssh root@$IP df -h | sed -n 's/.*\s\([0-9]*\)\%\s\/$/\1/p')
	        if [[ $DISK_USED -gt $THRESHOLD ]]
        	then
                	ssh root@$IP service httpd stop
	                ssh root@$IP "echo > /var/log/httpd/access_log"
        	        ssh root@$IP "echo > /var/log/httpd/error_log"
	                ssh root@$IP service httpd start
			date >> $LOG_FILE
	                echo "$IP cleared" >> $LOG_FILE
        	fi
		exit;
	done
}

echo "Started at " >> $LOG_FILE
date >> $LOG_FILE
clear_logs $VZ6_BASE_IP
clear_logs $KVM_BASE_IP

