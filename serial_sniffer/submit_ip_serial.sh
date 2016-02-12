#!/bin/bash
echo 'Submitting serial port'
IP=`ifconfig eth0 | grep 'inet addr' | awk '{ print $2 }'`
MAC=`ifconfig eth0 | grep 'HWaddr' | awk '{ print $5 }'`
echo [$MAC]$IP > /dev/ttyS0
