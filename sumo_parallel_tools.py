import os, errno
import time
import sys

colormaps = {
	'basic' : '#0:#168732,0.5:#ffffff,1:#c00000'
}
def do_open(filename):
	if not os.path.exists(os.path.dirname(filename)):
		try:
			os.makedirs(os.path.dirname(filename))
		except OSError as exc:  # Guard against race condition
			if exc.errno != errno.EEXIST:
				raise
	open(filename, 'w').close()
	return open(filename, 'r+')


current_milli_time = lambda: int(round(time.time() * 1000))
def get_sumo_home():
	if 'SUMO_HOME' in os.environ:
		sumo_home = os.environ['SUMO_HOME']
		tools = os.path.join(os.environ['SUMO_HOME'], 'tools')
		sys.path.append(tools)
	else:
		sys.exit("please declare environment variable 'SUMO_HOME'")
	return sumo_home