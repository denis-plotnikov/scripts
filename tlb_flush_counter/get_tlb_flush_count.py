#!/usr/bin/python
from subprocess import *
import re, time

counters = {
	"nr_tlb_remote_flush":0,
	"nr_tlb_remote_flush_received":0,
	"nr_tlb_local_flush_all":0,
	"nr_tlb_local_flush_one":0,
}


def get_counters():
	p = Popen("cat /proc/vmstat", stdout = PIPE, shell = True)
	out, _ = p.communicate()

	for key in counters.keys():
		pattern  = key + "\s*(\d+)"
		r = re.search(pattern, out)
		counters[key] = int(r.group(1))

##############################################################################
delimiter = "\t|\t"
i = 0
print ("-" * 80)
for key in counters.keys():
	i += 1
	print("[{0}] {1}".format(i, key))

print ("-" * 80)
header = "\t"
header += "time"
header += delimiter
for i in range(1, len(counters) + 1):
	header += "[{0}]".format(i)
	header += delimiter

print(header)
print ("-" * 80)

get_counters()

while(True):
	time.sleep(1)
	old_vals = dict()
	for key, value in counters.items():
		old_vals[key] = value
	get_counters()
	s = ""
	s += time.strftime("%H:%M:%S", time.gmtime())
	s += delimiter
	for key in counters.keys():
		s += str(counters[key] - old_vals[key])
		s += delimiter
	print(s)
