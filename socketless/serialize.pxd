# -*- Mode: Python; tab-width: 4; indent-tabs-mode: nil; -*-

cdef class MessageReader(object):
    cdef object message
    cdef public unsigned long i

    cdef inline object _read(self, unsigned long length)
    cdef inline object _read_string(self)
    cdef inline unsigned long read_int(self)
    cdef inline unsigned long read_int32(self)
    cdef inline unsigned long long read_int64(self)
    cpdef inline object read(self, unsigned long length=*)
    cpdef inline object read_string(self)

cdef class MarshallerGenerator(object):
    cpdef tuple compile(self, format)
    cdef compile_segment(self, segment)
    cdef unmarshalling_segments(self, format)
    cdef marshalling_segments(self, format)
