#!/usr/bin/python

import unittest
import subprocess
import inspect

txt_red = "\033[1;31m"
txt_green = "\033[1;32m"
txt_color_off ="\033[0;0m"

def exe(command):
	p = subprocess.Popen(command,
		stdout=subprocess.PIPE,
		stderr=subprocess.PIPE)
	out, _ = p.communicate()
	return out

def print_failed():
	print ("%s\t" + txt_red + "[FAILED]" + txt_color_off)\
		% inspect.stack()[1][3]

def print_success():
	print ("%s\t" + txt_green + "[SUCCESS]" + txt_color_off)\
		% inspect.stack()[1][3]

class TestMethods(unittest.TestCase):
	def test_cpu(self):
		output = exe(["cat", "/proc/cpuinfo"])
		try:
			self.assertTrue("cpsdasu" in output)
			print_success()
		except AssertionError:
			print_failed()

	def test_avx(self):
		output = exe(["cat", "/proc/cpuinfo"])
		try:
			self.assertTrue("avx" in output)
			print_success()
		except AssertionError:
			print_failed()

	def test_bvx(self):
		output = exe(["cat", "/proc/cpuinfo"])
		try:
			self.assertTrue("mmx" in output)
			print_success()
		except AssertionError:
			print_failed()


if __name__ == '__main__':
	unittest.main()
