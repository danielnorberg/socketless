import paths

from collections import deque
from timeit import default_timer as timer

from syncless import coio
from syncless.util import Queue

from messenger import Messenger

from utils.testcase import TestCase
from utils.channel_echoserver import launch_echoserver

class TestMessenger(TestCase):
	def testResilience(self):
		try:
			token = id(self)
			q = Queue()
			port = 6000
			host = ('localhost', port)
			p = launch_echoserver(port)
			coio.sleep(0.5)
			messenger = Messenger(host, 0.1)
			messenger.send('1', token, q)
			assert q.popleft() == ('1', token)
			p.kill()
			messenger.send('2', token, q)
			coio.sleep(0.5)
			messenger.send('3', token, q)
			assert q.popleft() == (None, token)
			assert q.popleft() == (None, token)
			p = launch_echoserver(port)
			coio.sleep(0.5)
			messenger.send('4', token, q)
			assert q.popleft() == ('4', token)
			messenger.close()
			coio.sleep(0.5)
		finally:
			p.kill()

	def testPerformance(self):
		token = id(self)
		message_length = 1024
		N = 10000
		batch_size = 100
		q = Queue()
		l = 0
		port = 6001
		host = ('localhost', port)
		p = launch_echoserver(port)
		bytecount = 0
		try:
			sent_messages = deque()
			coio.sleep(1)
			messenger = Messenger(host)
			message_buffer = ''.join('%d' % (i % 10) for i in xrange(N+message_length*2))
			i = 0
			start_time = timer()
			for i in xrange(N):
				if message_length > 4096:
					message = buffer(message_buffer, i, message_length)
				else:
					message = message_buffer[i:i+message_length]
				bytecount += len(message)
				messenger.send(message, token, q)
				sent_messages.append((message, token))
				l += 1
				if l % batch_size == 0:
					for j in xrange(batch_size):
						rm, rt = q.popleft()
						sm, st = sent_messages.popleft()
						if type(sm) is buffer:
							rm = buffer(rm)
						if rm != sm:
							print 'i: ', i
							assert False
			end_time = timer()
			elapsed_time = end_time - start_time
			print 'Transmitted %d messages with a size of %d bytes' % (N, message_length)
			print 'Transmission time (with validation): %fs' % elapsed_time
			print '%.2f requests+replies/s, %.2f MB/s' % (float(N*2) / elapsed_time, (float(bytecount*2) / 2**20) / elapsed_time)
			messenger.close()
		finally:
			p.kill()

if __name__ == '__main__':
	import unittest
	unittest.main()