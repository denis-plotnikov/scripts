#!/usr/bin/python

import numpy
import random

#input data
latency = 1 #s
size = 10

start_period = 1.0 * latency * size

#r = numpy.random.normal(start_period/2, start_period * 0.25, size)
r = numpy.random.beta(2, 2, size)
delays = r * start_period  # delays in seconds
#print(sorted(delays))
print(sorted(delays))

random.seed()
r = random.sample(range(latency * size * 1000), size)
print(sorted(r))
