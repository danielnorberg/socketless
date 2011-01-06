# -*- Mode: Python; tab-width: 4; indent-tabs-mode: nil; -*-

from messenger cimport Messenger
cdef class Broadcast:
	cdef public object messengers
	cdef object q
	cpdef send(self, message)
