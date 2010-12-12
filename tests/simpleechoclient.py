import syncless, syncless.patch
syncless.patch.patch_socket()

from syncless.util import Queue
from syncless import coio

import socket

import sys
import paths
sys.path.append(paths.home)

from channel import Channel, DisconnectedException
from timeit import default_timer as timer

def main():
	s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	s.connect(('127.0.0.1', 5555))

	c = Channel(s)
	message = 'Hello'
	N = 1000000
	start_time = timer()
	byte_count = N * len(message)
	l = 0
	for i in xrange(N):
		c.send(message)
		l += 1
		if l > 100:
			for j in xrange(l):
				c.recv()
			l = 0
	for j in xrange(l):
		c.recv()
	l = 0

	end_time = timer()
	diff_time = end_time - start_time
	print 'Transmission time: %fs' % diff_time
	print '%.2f messages/s, %.2f MB/s' % (float(N*2) / diff_time, (float(byte_count*2) / 2**20) / diff_time)

if __name__ == '__main__':
	main()