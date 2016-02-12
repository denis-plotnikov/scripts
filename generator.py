#! /usr/bin/python

def evens(last_number):
	for i in range(2, last_number + 1, 2):
		yield i


def main():
	for i in evens(7):
		print(i)


main()
