#!/usr/bin/python
import sys
import re
import json

class EventParser(object):
	def __init__(self, name, parser_func):
		self.name = name
		self.parser_func = parser_func
		self.parsed_data = dict() # list of dict entries in form of {name, val}

	def process_line(self, line):
		self.parser_func(line, self.parsed_data)
		
	def save_data(self, file_name):
		res = list()
		for data in self.parsed_data.items():
			d = dict()
			d["name"] = data[0]
			d["val"] = data[1]
			res.append(d)
		json_file = "{0}".format(file_name)
	        with open(json_file, "w") as f:
	               	json.dump(res, f)
	        print("{0} data saved to: {1}".format(self.name, json_file))


# parser functions
def one_value_parser_template(line, parser_data, reg_exp):
	v = re.search(reg_exp, line)
	if v:
                name = v.group(1)
		val = parser_data.get(name)
		if not val:
			val = 1
		else:
			val += 1
		
		parser_data[name] = val
		return True
	else:
		return False

def kvm_entry_parser(line, parser_data):
	return one_value_parser_template(line, parser_data, "kvm:kvm_entry:\s(\S+\s\d+)")

def kvm_exit_parser(line, parser_data):
	return one_value_parser_template(line, parser_data, "kvm:kvm_exit:\sreason\s(\S+)\s")

def kvm_mmio_parser(line, parser_data):
	return one_value_parser_template(line, parser_data, "kvm:kvm_mmio:\smmio\s(\S+)\s")

def kvm_userspace_exit_parser(line, parser_data):
	return one_value_parser_template(line, parser_data, "kvm:kvm_userspace_exit:\sreason\s(\S+)\s")

def kvm_emulate_insn_parser(line, parser_data):
	return one_value_parser_template(line, parser_data, "kvm:kvm_emulate_insn:\s\d+:\w+:(.*)\s\(\w+\)")

# avaliable events registration
EVENT_LIST = dict()

EVENT_LIST["kvm_entry"] = EventParser("kvm_entry", kvm_entry_parser)
EVENT_LIST["kvm_exit"] = EventParser("kvm_exit", kvm_exit_parser)
EVENT_LIST["kvm_mmio"] = EventParser("kvm_mmio", kvm_mmio_parser)
EVENT_LIST["kvm_userspace_exit"] = EventParser("kvm_userspace_exit", kvm_userspace_exit_parser)
EVENT_LIST["kvm_emulate_insn"] = EventParser("kvm_emulate_insn", kvm_emulate_insn_parser)

EVENT_NAMES = [EVENT_LIST.keys()]

# helper functions
def get_search_events_or_die(event_names):
	event_parsers = dict()
	try:
		for ename in event_names:
			 event_parsers[ename] = EVENT_LIST[ename]
	except KeyError as key_error:
		print("Unknown event: {0}".format(key_error.args[0]))
		sys.exit(1)
	return event_parsers


# event chain parsing
INSIDE_CHAIN_STATE = 1
OUTSIDE_CHAIN_STATE = 0

CHAIN_PARSER_DATA = dict()
CHAIN_PARSER_DATA["state"] = OUTSIDE_CHAIN_STATE
CHAIN_PARSER_DATA["name"] = None

def process_chain_line(line):
	r = re.search(":\skvm:(\w+):", line)
	if not r:
		return None

	event_name = r.group(1)

	result = None
	if event_name == "kvm_entry":
		if CHAIN_PARSER_DATA["state"] == INSIDE_CHAIN_STATE:
			CHAIN_PARSER_DATA["state"] = OUTSIDE_CHAIN_STATE
			result = "{0}->{1}".format(CHAIN_PARSER_DATA["name"], "kvm_entry")
			CHAIN_PARSER_DATA["name"] = None
		else:
			# it means we skip the rest of event records from the very beginning
			# in order to find the first kvm_exit and star chain parsing
			pass
	elif event_name == "kvm_exit":
		if CHAIN_PARSER_DATA["state"] == OUTSIDE_CHAIN_STATE:
			 CHAIN_PARSER_DATA["state"] = INSIDE_CHAIN_STATE
		reason_re = re.search("kvm:kvm_exit:\sreason\s(\S+)\s", line)
		reason = reason_re.group(1)
		CHAIN_PARSER_DATA["name"] = "{event_name}[{reason}]".format(event_name = event_name, reason = reason)
	elif event_name == "kvm_userspace_exit":
		reason_re = re.search("kvm:kvm_userspace_exit:\sreason\s(\S+)\s", line)
		reason = reason_re.group(1)
		CHAIN_PARSER_DATA["name"] = "{data}--{event_name}[{reason}]".format(data = CHAIN_PARSER_DATA["name"], event_name = event_name, reason = reason)
	elif event_name == "kvm_mmio":
                reason_re = re.search("kvm:kvm_mmio:\smmio\s(\S+)\s", line)
                reason = reason_re.group(1)
                CHAIN_PARSER_DATA["name"] = "{data}--{event_name}[{reason}]".format(data = CHAIN_PARSER_DATA["name"], event_name = event_name, reason = reason)
	else:
		CHAIN_PARSER_DATA["name"] = "{0}--{1}".format(CHAIN_PARSER_DATA["name"], event_name)

	return result

def parse_event_chain(file_name):
	event_chains = dict()

	with open(file_name, "r") as f:
		for line in f:
			chain_name = process_chain_line(line)
			if chain_name:
				val = event_chains.get(chain_name)
				if not val:
					val = 1
				else:
					val += 1
				event_chains[chain_name] = val

	# conver to list of dictionaries
	event_chains_list = list()
	for name, val in event_chains.items():
		d = dict()
		d["name"] = name
		d["val"] = val
		event_chains_list.append(d)

	event_chains_list = sorted(event_chains_list, key=lambda x: x["name"])
	json_file = "{source_file}.chains.json".format(source_file = file_name)
	with open(json_file, "w") as f:
		json.dump(event_chains_list, f)
	print("Event chains data saved to: {0}".format(json_file))
	print("Number of kvm_exit is [{0}]".format(sum([val for val in event_chains.values()])))


def main(file_name, event_names):
	event_parsers = get_search_events_or_die(event_names)

	# open file and pass a line to each parser available
	line_handlers = [ep.process_line for ep in event_parsers.values()]
	with open(file_name, "r") as f:
		for line in f:
			for handler in line_handlers:
				if handler(line):
					break
	
	# save parsers' data to separate files
	for event_parser in event_parsers.values():
		f = "{0}-{1}.json".format(file_name, event_parser.name)
		event_parser.save_data(f)


if __name__=="__main__":
	if len(sys.argv) != 3:
		print(
			'Usage: {0} file_name "event_name_0, ..., event_name_N"\nList of events avaliable: {1}\n'
			'	file_name: a file output of "perf script" command saved \n'
			'	event_name: an event name to be parsed'.
			format(sys.argv[0], EVENT_NAMES))
		sys.exit(1)

	events = sys.argv[2].split(',')
	event_names = map(lambda x: x.strip(), events)
	event_names = [event for event in event_names if event]
	main(sys.argv[1], event_names)
