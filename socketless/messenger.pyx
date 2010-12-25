__all__ = ['Messenger']

from syncless.best_stackless import stackless
from syncless import coio
from syncless.util import Queue
from collections import deque

import socket
import logging
from channel cimport Channel
from channel import Channel, DisconnectedException

cdef class Messenger:
	def __init__(self, listener, reconnect_max_interval=15):
		super(Messenger, self).__init__()
		self.reconnect_max_interval = reconnect_max_interval
		self.listener = listener
		self.socket = None
		self.channel = None
		self.response_queues = None
		self.send_queue = None
		self.sender = None
		self.receiver = None
		self.connector = coio.stackless.tasklet(self._connect)()
		self.disconnected = Queue()
		self.connected = False
		self.connect()

	def _connect(self):
		min_interval = 0.5
		while True:
			interval = min_interval
			self.disconnected.pop()
			while not self.socket:
				if self.connect():
					interval = min_interval
				else:
					coio.sleep(interval)
					interval = min(interval * 2, self.reconnect_max_interval)

	cpdef connect(self):
		try:
			s = coio.nbsocket(socket.AF_INET, socket.SOCK_STREAM)
			s.connect(self.listener)
			self.socket = s
			self.channel = Channel(self.socket)
			self.response_queues = deque()
			self.send_queue = Queue()
			self.sender = stackless.tasklet(self._send)()
			self.receiver = stackless.tasklet(self._recv)()
			self.connected = True
			return True
		except socket.error, e:
			self._handle_disconnection(e)
			return False

	def _handle_disconnection(self, e):
		"""docstring for handle_error"""
		logging.warning(e)
		self._teardown()
		self.disconnected.append(True)

	def _teardown(self):
		self.connected = False
		if self.sender and self.sender != coio.stackless.getcurrent():
			self.sender.kill()
			self.sender = None
		if self.receiver and self.receiver != coio.stackless.getcurrent():
			self.receiver.kill()
			self.receiver = None
		self.channel = None
		if self.socket:
			self.socket.close()
			self.socket = None
		if self.response_queues:
			for token, response_queue in self.response_queues:
				response_queue.append((None, token))
		self.send_queue = None
		self.response_queues = None

	def _send(self):
		while True:
			try:
				while True:
					message = self.send_queue.popleft()
					self.channel.send(message)
					if len(self.send_queue) == 0:
						break
				self.channel.flush()
			except DisconnectedException, e:
				self._handle_disconnection(e)
				return

	def _recv(self):
		while True:
			try:
				message = self.channel.recv()
				token, response_queue = self.response_queues.popleft()
				response_queue.append((message, token))
			except DisconnectedException, e:
				self._handle_disconnection(e)
				return

	cpdef send(self, message, token, response_queue):
		if self.connected:
			self.send_queue.append(message)
			self.response_queues.append((token, response_queue))
		else:
			response_queue.append((None, token))

	cpdef close(self):
		self.connector.kill()
		if self.connected:
			try:
				self.channel.close()
			except DisconnectedException:
				pass
		self._teardown()
