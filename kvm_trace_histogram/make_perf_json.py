#!/usr/bin/python
import re
import json
import sys
import subprocess

DEFAULT_TIME_SEC = 30


def main(pid, time_sec):
	print("Rcording PID: {0}".format(pid))
	cmd = 'perf record -p {0} -e "kvm:*" sleep {1}'.format(pid, time_sec)
	print(cmd)
	subprocess.check_call(cmd, shell=True)
	file_base_name = "/tmp/perf_pid{0}".format(pid)

	# save report file
	txt_file = "{0}.txt".format(file_base_name)
	report_cmd = 'perf report > {0}'.format(txt_file)
	subprocess.check_call(report_cmd, shell=True)

	# save report script - a report file with detailed event info
	script_file = "{0}.script.txt".format(file_base_name)
	script_cmd = 'perf script > {0}'.format(script_file)
	subprocess.check_call(script_cmd, shell=True)
	
	# parse report file
	with open(txt_file, "r") as f:
		content = f.read()

	search_res = re.findall("# Samples:.+of event.+\n# Event count \(approx\.\): \d+", content)

	res = list()
	for line in search_res:
		v = re.match("# Samples:.+of event.+'(\S+)'\n# Event count \(approx\.\): (\d+)", line)
		if v:
			point = dict()
			point["name"] = v.group(1)[4:]
			point["val"] = int(v.group(2))/time_sec
		res.append(point)

	res = sorted(res, key=lambda x: x["name"])

	#for point in res:
	#	print("{0} -- {1}".format(point["name"], point["val"]))

	json_file = "{0}.json".format(file_base_name)
	with open(json_file, "w") as f:
		json.dump(res, f)

	print("Parsed data saved to: {0}".format(json_file))
	print("Report saved to: {0}".format(txt_file))
	print("Detailed report saved to: {0}".format(script_file))

	#with open("out.json", "r") as f:
	#	d = json.load(f)
	#
	#	print(d)
	#	for point in d:
	#		print("{0} -- {1}".format(point["name"], point["val"]))

if __name__=="__main__":
	time_sec = DEFAULT_TIME_SEC
	if len(sys.argv) == 1:
		print("Usage: {0} <pid> [time_of_recording_sec]".format(sys.argv[0][2:]))
		sys.exit(1)
	elif len(sys.argv) == 3:
		time_sec = int(sys.argv[2])
	main(sys.argv[1], time_sec)
