#!/bin/python
import sys, serial, threading, signal, time
from optparse import OptionParser

SNIFF_THREADS = list()
log_file = "serial.out" #output file name
f = None #file
go = True

def stop(signal, frame):
	global go
	global f
	print('\nGot stop signal')
	go = False
	# waiting for threads to stop
	print("Waiting for the threads to finish")
	for thread in SNIFF_THREADS:
		thread.join()
	
	# close the file
	f.close()
	print("Done")
	sys.exit(0)

def listen(serial_port, l_file):
	global go
	s = serial.Serial(serial_port, 19200, timeout = 1)
	while go:
		out = s.read(256)
		out = out.strip()
		if len(out) > 0:
			l_file.write(out + "\n")
			l_file.flush()

def main(argv):
	global log_file
	usage = "usage: %prog [options] path_to_serial_0, path_to_serial_1, ..."
	parser = OptionParser(usage)
	parser.add_option("-f", "--file", dest = "filename",
			help = "write output to file FILE, default:{0}".format(log_file),
			metavar = "FILE")
	(options, args) = parser.parse_args()
	
	if len(args) == 0:
		parser.error("At least one path to serial console must be specified")
		sys.exit(1)

	if options.filename:
		log_file = options.filename
	
	signal.signal(signal.SIGINT, stop)
	signal.signal(signal.SIGTERM, stop)
	global f
	f = open(log_file, "w")

	for port in args:
		t = threading.Thread(target = listen, args = (port, f))
		SNIFF_THREADS.append(t)
	
	for thread in SNIFF_THREADS:
		thread.start()
	print("Listening threads started")
	while True:
		time.sleep(60)
	

if __name__ == "__main__":
	main(sys.argv)
