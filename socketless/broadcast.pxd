from messenger cimport Messenger
cdef class Broadcast:
	cdef public object messengers
	cdef object q
	cpdef send(self, message)
