import gevent
import gevent.monkey
gevent.monkey.patch_all()
from gevent.queue import Queue
from gevent.event import Event
from collections import deque

import socket
import logging
from channel import Channel, DisconnectedException
from utils.testcase import TestCase

class Messenger(object):
	def __init__(self, listener):
		super(Messenger, self).__init__()
		self.listener = listener
		self.socket = None
		self.channel = None
		self.response_queues = None
		self.send_queue = None
		self.sender = None
		self.receiver = None
		self.connector = gevent.spawn(self._connect)
		self.disconnected = Event()
		self.connected = False
		self.connect()

	def _connect(self):
		while True:
			self.disconnected.wait()
			while not self.socket:
				if self.connect():
					self.disconnected.clear()
				else:
					gevent.sleep(0.1)

	def connect(self):
		try:
			s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
			s.connect(self.listener)
			self.socket = s
			self.channel = Channel(self.socket)
			self.response_queues = deque()
			self.send_queue = Queue()
			self.sender = gevent.spawn(self._send)
			self.receiver = gevent.spawn(self._recv)
			self.connected = True
			return True
		except socket.error, e:
			self._handle_disconnection(e)
			return False

	def _handle_disconnection(self, e):
		"""docstring for handle_error"""
		logging.error(e)
		self._teardown()
		self.disconnected.set()

	def _teardown(self):
		self.connected = False
		if self.sender and self.sender != gevent.getcurrent():
			self.sender.kill()
			self.sender = None
		if self.receiver and self.receiver != gevent.getcurrent():
			self.receiver.kill()
			self.receiver = None
		self.channel = None
		if self.socket:
			self.socket.close()
			self.socket = None
		if self.response_queues:
			for token, response_queue in self.response_queues:
				response_queue.put((None, token))
		self.send_queue = None
		self.response_queues = None

	def _send(self):
		while True:
			message = self.send_queue.get()
			try:
				self.channel.send(message)
				self.channel.flush()
			except DisconnectedException, e:
				self._handle_disconnection(e)
				return

	def _recv(self):
		while True:
			try:
				message = self.channel.recv()
				token, response_queue = self.response_queues.popleft()
				response_queue.put((message, token))
			except DisconnectedException, e:
				self._handle_disconnection(e)
				return

	def send(self, message, token, response_queue):
		if self.connected:
			self.send_queue.put(message)
			self.response_queues.append((token, response_queue))
		else:
			response_queue.put((None, token))

	def close(self):
		self.connector.kill()
		if self.connected:
			try:
				self.channel.close()
			except DisconnectedException:
				pass
		self._teardown()

class TestMessenger(TestCase):
	def testResilience(self):
		from tests import echoserver
		try:
			token = id(self)
			q = Queue()
			port = 6000
			host = ('localhost', port)
			p = echoserver.launch_echoserver(port)
			gevent.sleep(0.5)
			messenger = Messenger(host)
			messenger.send('1', token, q)
			assert q.get() == ('1', token)
			assert not messenger.response_queues
			p.kill()
			messenger.send('2', token, q)
			gevent.sleep(0.5)
			messenger.send('3', token, q)
			assert q.get() == (None, token)
			assert q.get() == (None, token)
			assert not messenger.response_queues
			p = echoserver.launch_echoserver(port)
			gevent.sleep(0.5)
			messenger.send('4', token, q)
			assert q.get() == ('4', token)
			messenger.close()
			gevent.sleep(0.5)
		finally:
			p.kill()

	def testPerformance(self):
		from tests import echoserver
		from timeit import default_timer as timer
		token = id(self)
		N = 10000
		q = Queue()
		l = 0
		port = 6001
		host = ('localhost', port)
		p = echoserver.launch_echoserver(port)
		bytecount = 0
		try:
			gevent.sleep(0.5)
			messenger = Messenger(host)
			start_time = timer()
			for i in xrange(N):
				message = str(i)*1024
				bytecount += len(message)
				messenger.send(message, token, q)
				l += 1
				if l > 100:
					for j in xrange(l):
						q.get()
					l = 0
			end_time = timer()
			diff_time = end_time - start_time
			print 'Transmission time: %fs' % diff_time
			print '%.2f messages/s, %.2f MB/s' % (float(N) / diff_time, (float(bytecount) / 2**20) / diff_time)
			messenger.close()
		finally:
			p.kill()


if __name__ == '__main__':
	import unittest
	unittest.main()
