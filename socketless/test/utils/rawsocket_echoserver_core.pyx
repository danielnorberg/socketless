# -*- Mode: Python; tab-width: 4; indent-tabs-mode: nil; -*-

from socketless.channel cimport Channel
from socketless.channel import Channel, DisconnectedException

cpdef receiver(Channel c):
	cdef object message
	while True:
		message = c.recv()
		if not message:
			break
		c.send(message)
		c.flush()
