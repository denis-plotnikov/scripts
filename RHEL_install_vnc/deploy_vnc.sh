#!/bin/bash
yum install libvirt virt-manager virt-clone tigervnc tigervnc-server
yum install *gnome*
rm -f /etc/systemd/system/vncserver@.service
rm -f /etc/systemd/system/vncserver@:1.service
cp vncserver@.service /etc/systemd/system/vncserver@.service
cp vncserver@.service /etc/systemd/system/vncserver@:1.service
mkdir /root/.vnc
systemctl deamon-reload
vncpasswd
systemctl start vncserver@:1.service
systemctl enable vncserver@:1.service


