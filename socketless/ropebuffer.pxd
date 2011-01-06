# -*- Mode: Python; tab-width: 4; indent-tabs-mode: nil; -*-

cdef class RopeBuffer:
	cdef int i
	cdef public int len
	cdef object ropes
	cpdef add(self, data)
	cpdef _read(self, int length)
	cpdef read(self, int length)
	cpdef drain(self)
