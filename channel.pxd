cdef class Channel:
	cdef object socket
	cdef object buffer
	cdef object send_buffer
	cpdef send(self, message)
	cpdef flush(self)
	cpdef recv(self)
	cpdef close(self)
