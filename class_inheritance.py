#!/usr/bin/python

class A(object):
	def __init__(self):
		print("A's __init__")

class B(A):
	def __init__(self):
		A.__init__(self)
		print("B's __init__")

b = B()
