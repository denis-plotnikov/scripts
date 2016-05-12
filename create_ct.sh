#!/bin/bash
#ls /vz/template/cache/ - get cached template list
#prlsrvctl net list     - get list of networks
# creates and tune a container on Virtuozzo server platform
ct_name=$1 
prlctl create $ct_name --ostemplate centos-7-x86_64 --vmtype ct
prlctl set $ct_name --cpus 2 --memsize 8G
prlctl set $ct_name --device-set hdd0 --size 64G
prlctl set $ct_name --device-add net --network Bridged --dhcp yes
prlctl set $ct_name --userpasswd root:1q2w3e
prlctl set $ct_name --hostname ${ct_name}.sw.ru




