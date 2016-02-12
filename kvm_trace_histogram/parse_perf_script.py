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
		res.append(self.parsed_data)
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

# avaliable events registration
EVENT_LIST = dict()

EVENT_LIST["kvm_entry"] = EventParser("kvm_entry", kvm_entry_parser)
EVENT_LIST["kvm_exit"] = EventParser("kvm_exit", kvm_exit_parser)

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
		print('Usage: {0} file_name "event_name_0, ..., event_name_N"\nList of events avaliable: {1}'.
			format(sys.argv[0], EVENT_NAMES))
		sys.exit(1)

	events = sys.argv[2].split(',')
	event_names = map(lambda x: x.strip(), events)
	event_names = [event for event in event_names if event]
	main(sys.argv[1], event_names)
