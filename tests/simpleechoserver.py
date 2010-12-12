from syncless.util import Queue
from syncless import coio

import sys
import paths
sys.path.append(paths.home)

from streamserver import StreamServer
from channel import Channel, DisconnectedException

class EchoServer(StreamServer):
	"""docstring for Handler"""
	def __init__(self, listener):
		super(EchoServer, self).__init__(listener)
		print 'started'

	def receiver(self, c):
		while True:
			message = c.recv()
			if not message:
				break
			c.send(message)

	def handle_connection(self, s, address):
		print 'New connection from %s:%s' % address
		try:
			c = Channel(s)
			self.receiver(c)
			c.close()
		except DisconnectedException:
			print 'Client disconnected'


def main():
    server = EchoServer(('127.0.0.1', 5555))

if __name__ == '__main__':
    main()