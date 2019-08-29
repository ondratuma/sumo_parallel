from xml.dom import minidom
import unicodedata
import itertools
import sys
import subprocess
import os
from sumo_parallel_tools import get_sumo_home, do_open

sumo_home = get_sumo_home()

def get_filenames():
	try:
		return sys.argv[1], sys.argv[2], sys.argv[3]
	except IndexError:
		return sys.exit("need 2 input files and one output")

def diffEdges(edge1, edge2, output_edge):
	attributes = [edge1.attributes.items(),
	              edge2.attributes.items()]
	attribute_names = [[i[0] for i in attributes[0]],
	                   [i[0] for i in attributes[1]]]
	all_attribute_names_for_edge = list(set(attribute_names[0] + attribute_names[1]))

	for attribute_name in all_attribute_names_for_edge:
		if attribute_name == "id":
			output_value = edge1.attributes[attribute_name].value
		else:
			try:
				att1_value = edge1.attributes[attribute_name].value
			except KeyError:
				att1_value = 0
			try:
				att2_value = edge2.attributes[attribute_name].value
			except KeyError:
				att2_value = 0
			output_value = str(float(att1_value) - float(att2_value))
		output_edge.setAttribute(attribute_name, output_value)
	return output_edge

def diffEdgeFiles(file1,file2,output_filename):
	output_file = open(output_filename, "w+")
	output = minidom.Document()
	meandata = output.createElement('meandata')
	output.appendChild(meandata)
	files = [minidom.parse(file1),
	         minidom.parse(file2)]
	intervals = itertools.zip_longest(files[0].getElementsByTagName('interval'),
	                                  files[1].getElementsByTagName('interval'))
	for interval1, interval2 in intervals:
		if interval1.attributes['id'].value == interval2.attributes['id'].value:
			interval = output.createElement('interval')
			for attribute in interval1.attributes.items():
				interval.setAttribute(attribute[0], attribute[1])
			meandata.appendChild(interval)
			edges = itertools.zip_longest(interval1.getElementsByTagName("edge"), interval2.getElementsByTagName("edge"))
			for edge_open, edge_closed in edges:
				output_edge = output.createElement('edge')
				output_edge = diffEdges(edge_open, edge_closed, output_edge)
				interval.appendChild(output_edge)
	output_file.write(output.toxml())
def plotEdgeFile(input_filename, netfile, output_filename, metric, colormap):
	do_open(output_filename).close()
	script = os.path.join(sumo_home, 'tools', 'visualization','plot_net_dump.py')
	plot_net_dump_settings = ["python3", script, '-i', ','.join((input_filename, input_filename)), '-n', netfile,
	                          '--output', output_filename, '--measures', metric + ',' + metric,'--title=' + metric,'--colormap',colormap,'--xticks=0,0,1,1','--yticks=0,0,1,1','--size=38.40,21.60'
	]
	print(plot_net_dump_settings)
	plot_net_dump = subprocess.Popen(plot_net_dump_settings)
def main():
	filename1, filename2, output_filename = get_filenames()
	diffEdgeFiles(filename1,filename2,output_filename)
	plotEdgeFile(output_filename, "grid/grid.net.xml" ,'grid.png', "entered",colormaps[0])
if __name__ == '__main__':
	main()