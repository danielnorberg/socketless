from syncless.util import Queue
from syncless import coio

import subprocess
import argparse

import paths

from streamserver import StreamServer
from channel import Channel, DisconnectedException

def launch_echoserver(port):
	path = paths.path('test/utils/channel_echoserver.py')
	cmd = 'python %s %d %d' % (path, port, port)
	return subprocess.Popen(cmd, shell=True)

class EchoServer(StreamServer):
	"""docstring for Handler"""
	def __init__(self, listener):
		super(EchoServer, self).__init__(listener)
		print 'started'

	def sender(self, q, c, f):
		i = 0
		try:
			while True:
				i += 1
				message = q.popleft()
				if not message:
					break
				c.send(message)
				if len(q) == 0:
					c.flush()
		except DisconnectedException:
			pass
		finally:
			f.append(True)

	def receiver(self, q, c, f):
		i = 0
		try:
			while True:
				i += 1
				message = c.recv()
				q.append(message)
				if not message:
					break
		except DisconnectedException:
			print 'Client disconnected'
		finally:
			f.append(True)

	def handle_connection(self, s, address):
		print 'New connection from %s:%s' % address
		c = Channel(s)
		q = Queue()
		f = Queue()
		coio.stackless.tasklet(self.sender)(q, c, f)
		coio.stackless.tasklet(self.receiver)(q, c, f)
		f.popleft()
		f.popleft()
		try:
			c.close()
			print 'Connection closed'
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
			print 'q to quit'
			if raw_input() == 'q':
				break
		for process in processes:
			process.kill()
		sys.exit(0)


if __name__ == '__main__':
	try:
		main()
	except KeyboardInterrupt:
		print