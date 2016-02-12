#!/usr/bin/python

from optparse import OptionParser

def main():
	parser = OptionParser()
	parser.add_option("-f", "--file",
			dest="file_name", help="specifies output file",
			metavar="FILE")

	parser.add_option("-v", "--verbose",
			dest="verbose", help="activates verbose output",
			default=False, action="store_true")

	parser.add_option("-n", "--num_iter", type="int",
			dest="num_iterations", help="number of iterations",
			default=1, metavar="NUMBER")

	(options, args) = parser.parse_args()

	print options
	print args

	print "="*80
	print options.file_name
	print options.verbose
	print options.num_iterations

main()
