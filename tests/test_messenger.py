import sys
import paths
sys.path.append(paths.home)

from collections import deque

from syncless import coio
from syncless.util import Queue

from messenger import Messenger

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