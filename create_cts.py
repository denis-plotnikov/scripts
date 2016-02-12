#!/usr/bin/python
import sys, os

def list():
	os.system("vzpkg list -O --with-summary")

def create_centos():
	os.system("prlctl create test_ct --ostemplate centos-6-x86_64 --vmtype ct")

def add_netif(ctid):
	os.system("prlctl set {0} --netif_add eth1"\
			.format(ctid))
	os.system("prlctl set {0} --ifname eth1 --dhcp yes"\
			.format(ctid))

def add_if():
	add_netif(107)

def menu():
	actions = {
		"exit": sys.exit,
		"list": list,
		"centos": create_centos,
		"add_if": add_if
	}
	while True:
		user_input = raw_input(">> ")
		try:
			actions[user_input]()
		except KeyError:
			print("\"{0}\" is not supported"
					.format(user_input))

if __name__ == "__main__":
	menu()
