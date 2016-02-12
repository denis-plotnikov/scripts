#! /usr/bin/python
import time

def measure(f):
	start_time = time.clock()
	f()
	end_time = time.clock() - start_time
	print ("Elapsed time: {0} sec".format(end_time))

def sum_gen():
	print sum(x for x in range(1, int(1e8)))


def sum_iter():
	print sum([x for x in range(1, int(1e8))])

def hello():
	print "Hello!"

def main():
	measure(sum_gen)
	measure(sum_iter)

if __name__ == "__main__":
	main()
