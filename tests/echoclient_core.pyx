from channel cimport Channel
from channel import Channel

cpdef sender(Channel c, message, int N, f):
	cdef int i
	for i in xrange(N):
		c.send(message)
		c.flush()
	f.append(True)

cpdef receiver(Channel c, int N, f):
	for i in xrange(N):
		c.recv()
	f.append(True)
