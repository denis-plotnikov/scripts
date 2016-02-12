#!/usr/bin/python

import subprocess

START_CTID = 108
END_CTID = 115

def exe(command):
	p = subprocess.Popen(command,
		stdout=subprocess.PIPE,
		stderr=subprocess.PIPE)
	out, _ = p.communicate()
	return out

def stop_ct(ctid):
	exe(["vzctl", "stop", str(ctid)])

def delete_ct(ctid):
	exe(["vzctl", "delete", str(ctid)])

def main():
	for ctid in range(START_CTID, END_CTID + 1):
		stop_ct(ctid)
		delete_ct(ctid)

	print exe(["vzlist", "-a", "-n"])


if __name__ == '__main__':
	main()
