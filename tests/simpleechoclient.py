import syncless, syncless.patch
syncless.patch.patch_socket()

from syncless.util import Queue
from syncless import coio

import socket

import sys
import paths
sys.path.append(paths.home)

from timeit import default_timer as timer

from channel import Channel
import echoclient_core

def main():
	s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	s.connect(('127.0.0.1', 5555))
	c = Channel(s)
	N = 200000
	M = 16
	message = '.' * M
	byte_count = len(message) * N
	f = Queue()
	coio.stackless.tasklet(echoclient_core.sender)(c, message, N, f)
	coio.stackless.tasklet(echoclient_core.receiver)(c, N, f)
	start_time = timer()
	f.pop()
	f.pop()
	end_time = timer()
	diff_time = end_time - start_time
	print 'Transmission time: %fs' % diff_time
	print '%.2f messages/s, %.2f MB/s' % (float(N*2) / diff_time, (float(byte_count*2) / 2**20) / diff_time)

if __name__ == '__main__':
	main()