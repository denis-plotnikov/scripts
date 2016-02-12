#!/usr/bin/python

import unittest
import subprocess
import inspect
import re

txt_red = "\033[1;31m"
txt_green = "\033[1;32m"
txt_color_off ="\033[0;0m"

def exe(command):
	try:
		p = subprocess.Popen(command,
		stdout=subprocess.PIPE,
		stderr=subprocess.PIPE)
		out, _ = p.communicate()
	except:
		print ("Error occured during command execution")
		print ("Command: {0}".format(" ".join(command)))
		raise
	else:
		return out

def print_failed():
	print ("%s\t" + txt_red + "[FAILED]" + txt_color_off)\
		% inspect.stack()[1][3]

def print_success():
	print ("%s\t" + txt_green + "[SUCCESS]" + txt_color_off)\
		% inspect.stack()[1][3]

class TestMethods(unittest.TestCase):
	def test_single_url(self):
		try:
			command = ["/home/denis/tests/atomic/bin/lin64/httpress",\
					"-t", "10", "http://10.30.17.179/index1.html"]
			output = exe(command)
		
			self.assertTrue("URL#000 |" in output)
			print_success()
			print(output)
			test_result = re.search("\{\s[0-9]+\.[0-9]+\s\}", output)
			res = test_result.group()
			rate = float(res[2:-2])
			if rate == 0:
				raise Exception("Rate: 0 looks suspicious!")
			print(rate)
		except Exception:
			print_failed()

if __name__ == '__main__':
	unittest.main()
