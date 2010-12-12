import syncless, syncless.patch
syncless.patch.patch_socket()
from syncless.best_stackless import stackless
from syncless import coio
from syncless.util import Queue
from collections import deque

import socket
import logging
from channel import Channel, DisconnectedException

class Messenger(object):
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

	def connect(self):
		try:
			s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
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
		logging.error(e)
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

	def send(self, message, token, response_queue):
		if self.connected:
			self.send_queue.append(message)
			self.response_queues.append((token, response_queue))
		else:
			response_queue.append((None, token))

	def close(self):
		self.connector.kill()
		if self.connected:
			try:
				self.channel.close()
			except DisconnectedException:
				pass
		self._teardown()


from utils.testcase import TestCase

class TestMessenger(TestCase):
	# def testResilience(self):
	# 	from tests import echoserver
	# 	try:
	# 		token = id(self)
	# 		q = Queue()
	# 		port = 6000
	# 		host = ('localhost', port)
	# 		p = echoserver.launch_echoserver(port)
	# 		coio.sleep(0.5)
	# 		messenger = Messenger(host, 0.1)
	# 		messenger.send('1', token, q)
	# 		assert q.popleft() == ('1', token)
	# 		assert not messenger.response_queues
	# 		p.kill()
	# 		messenger.send('2', token, q)
	# 		coio.sleep(0.5)
	# 		messenger.send('3', token, q)
	# 		assert q.popleft() == (None, token)
	# 		assert q.popleft() == (None, token)
	# 		assert not messenger.response_queues
	# 		p = echoserver.launch_echoserver(port)
	# 		coio.sleep(0.5)
	# 		messenger.send('4', token, q)
	# 		assert q.popleft() == ('4', token)
	# 		messenger.close()
	# 		coio.sleep(0.5)
	# 	finally:
	# 		p.kill()

	def testPerformance(self):
		# from pudb import set_trace; set_trace()
		from tests import echoserver
		from timeit import default_timer as timer
		token = id(self)
		N = 100000
		q = Queue()
		l = 0
		port = 6001
		host = ('localhost', port)
		p = echoserver.launch_echoserver(port)
		bytecount = 0
		try:
			sent_messages = deque()
			coio.sleep(1)
			messenger = Messenger(host)
			start_time = timer()
			message_length = 1024
			message_buffer = ''.join('%d' % (i % 10) for i in xrange(N+message_length*2))
			for i in xrange(N):
				message = message_buffer[i:i+message_length]
				bytecount += len(message)
				messenger.send(message, token, q)
				sent_messages.append((message, token))
				l += 1
				if l > 100:
					for j in xrange(l):
						rm, rt = q.popleft()
						sm, st = sent_messages.popleft()
						if rm != sm:
							print 'i: ', i
							print 'rm: %s, rt: %s ' % (rm, rt)
							print 'sm: %s, st: %s' % (sm, st)
							assert False
					l = 0
			end_time = timer()
			diff_time = end_time - start_time
			print 'Transmission time: %fs' % diff_time
			print '%.2f messages/s, %.2f MB/s' % (float(N*2) / diff_time, (float(bytecount*2) / 2**20) / diff_time)
			messenger.close()
		finally:
			p.kill()


if __name__ == '__main__':
	import unittest
	unittest.main()
