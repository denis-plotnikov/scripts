#!/usr/bin/python
import os, time

def main():
	while True:
		os.system("vzlist -a -n | grep infrastruct")
		time.sleep(1)


if __name__ == "__main__":
	main()
