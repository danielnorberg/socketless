from ropebuffer cimport RopeBuffer
cdef class Channel:
	cdef object socket
	cdef RopeBuffer buffer
	cdef object send_buffer
	cdef object unpack
	cdef object pack
	cdef object header_spec
	cdef bint flushing
	cpdef connect(self, listener)
	cpdef send(self, message)
	cpdef flush(self)
	cpdef recv(self)
	cpdef close(self)
