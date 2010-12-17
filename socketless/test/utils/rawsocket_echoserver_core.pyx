from streamserver import StreamServer
from channel cimport Channel
from channel import Channel, DisconnectedException

cpdef receiver(Channel c):
	cdef object message
	while True:
		message = c.recv()
		if not message:
			break
		c.send(message)
