from channel cimport Channel
cdef class Messenger:
	cdef int reconnect_max_interval
	cdef object listener
	cdef object socket
	cdef Channel channel
	cdef object response_queues
	cdef object send_queue
	cdef object sender
	cdef object receiver
	cdef object connector
	cdef object disconnected
	cdef bint connected
	cpdef connect(self)
	cpdef send(self, message, token, response_queue)
	cpdef close(self)