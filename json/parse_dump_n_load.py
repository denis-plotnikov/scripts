#!/usr/bin/python
import re
import json

with open("idle.txt", "r") as f:
	content = f.read()

m = re.findall("# Samples:.+of event.+\n# Event count \(approx\.\): \d+", content)

res = list()
for line in m:
	print(line)
	v = re.match("# Samples:.+of event.+'(\S+)'\n# Event count \(approx\.\): (\d+)", line)
	if v:
		print(v.group())
		point = dict()
		point["name"] = v.group(1)[4:]
		point["val"] = v.group(2)

		res.append(point)

res = sorted(res, key=lambda x: x["name"])

for point in res:
	print("{0} -- {1}".format(point["name"], point["val"]))

with open("out.json", "w") as f:
	json.dump(res, f)


with open("out.json", "r") as f:
	d = json.load(f)

print(d)
for point in d:
	print("{0} -- {1}".format(point["name"], point["val"]))
