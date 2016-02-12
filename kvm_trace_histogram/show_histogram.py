#!/usr/bin/python
#import plotly.plotly as py
#import plotly.graph_objs as go
import sys
import json
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.lines import Line2D


def get_points(points):
	names = [point["name"] for point in points]
	vals = [int(point["val"]) for point in points]
	r = dict()
	r["names"] = names
	r["vals"] = vals
	return r

def make_histograms(files_list):
	point_sets = list()
	for file_name in files_list:
		with open(file_name, "r") as f:
			loaded_list = json.load(f)
	        	point_sets.append(get_points(loaded_list))

	fig, ax = plt.subplots()	
	plt.gca().set_ylim(bottom=0)
	width = 1
	alpha = 0.4
	def annotate(vals, y_pos, shift):
		for i, j in zip(vals, y_pos):
			if i: 
				ax.annotate(
					'{0}'.format(i),
					xy = (i,j),
					xytext = (5, width/4),
					textcoords='offset points',
					fontsize = 8)
	names = point_sets[0]["names"]
	y_pos = np.arange(len(names))
	y_pos = y_pos * 4
	colors = ['r', 'y', 'g', 'b']

	legend_items = list()
	for i in range(len(point_sets)):
		vals = point_sets[i]["vals"]
		yp = y_pos + width * i
		c = colors[i % len(colors)]
		bar = ax.barh(
				yp, vals, width,
				align= 'center',
				color= c,
				alpha= alpha,
				label = files_list[i])
		annotate(vals, yp, i)
		l = Line2D([], [], linewidth = 6, color = c, alpha = alpha)
		legend_items.append(l)

	leg = ax.legend(legend_items, files_list)
	plt.yticks(y_pos, names, fontsize = 10)
	plt.show()

if __name__=="__main__":
	make_histograms(sys.argv[1:])
