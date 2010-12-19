from syncless import coio

import socket

class StreamServer(object):
	"""docstring for StreamServer"""
	def __init__(self, listener, listen_backlog=1024):
		super(StreamServer, self).__init__()
		s = coio.nbsocket(socket.AF_INET, socket.SOCK_STREAM)
		s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
		s.bind(listener)
		s.listen(listen_backlog)
		while True:
			conn, addr = s.accept()
			coio.stackless.tasklet(self.handle_connection)(conn, addr)
			coio.stackless.schedule()
