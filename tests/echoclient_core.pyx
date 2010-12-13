from channel cimport Channel
from channel import Channel

from syncless import coio

cpdef sender(Channel c, message, int N, f):
	cdef int i
	cdef int l = 0
	for i in xrange(N):
		c.send(message)
		c.flush()
		if i % 100 == 0:
			coio.stackless.schedule()
	f.append(True)

cpdef receiver(Channel c, int N, f):
	for i in xrange(N):
		c.recv()
	f.append(True)
