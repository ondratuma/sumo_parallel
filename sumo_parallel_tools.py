import os, errno
import time
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