import gevent
import gevent.monkey
gevent.monkey.patch_all()

import subprocess
import argparse

from gevent.server import StreamServer
from gevent.queue import Queue

import sys
import paths
sys.path.append(paths.home)

from channel import Channel, DisconnectedException

def launch_echoserver(port):
	path = paths.path('tests/echoserver.py')
	cmd = 'python %s %d %d' % (path, port, port)
	return subprocess.Popen(cmd, shell=True)

class EchoServer(StreamServer):
	"""docstring for Handler"""
	def __init__(self, listener):
		super(EchoServer, self).__init__(listener, self.handle_connection)
		self.q = Queue()
		print 'started'

	def receiver(self, c):
		i = 0
		while True:
			i += 1
			message = c.recv()
			if not message:
				c.close()
				break
			c.send(message)
			if i % 1000 == 0:
				gevent.sleep()

	def handle_connection(self, s, address):
		print 'New connection from %s:%s' % address
		c = Channel(s)
		try:
			self.receiver(c)
		except DisconnectedException:
			print 'Client disconnected'

def main():
	parser = argparse.ArgumentParser(description="Echo Server")
	parser.add_argument('port_range_start', type=int)
	parser.add_argument('port_range_end', type=int)
	args = parser.parse_args()
	if args.port_range_start == args.port_range_end:
		print 'Starting server on port %d' % args.port_range_start
		EchoServer(('0.0.0.0', args.port_range_start)).serve_forever()
	else:
		processes = [launch_echoserver(port)	for port in xrange(args.port_range_start, args.port_range_end + 1)]
		while True:
			raw_input()
		for process in processes:
			process.kill()


if __name__ == '__main__':
	try:
		main()
	except KeyboardInterrupt:
		print