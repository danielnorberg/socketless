# -*- Mode: Python; tab-width: 4; indent-tabs-mode: nil; -*-

from channel cimport Channel

cpdef invoke_all(message, messengers)
cpdef send_all(message, messengers, collector)

cdef class Collector:
    cdef unsigned int item_count
    cdef unsigned int wait_amount
    cdef list items
    cdef object wait_queue
    cpdef collect(self)

cdef class Messenger:
    cdef int reconnect_max_interval
    cdef object listener
    cdef object handshake
    cdef Channel channel
    cdef object callbacks
    cdef object send_queue
    cdef object sender
    cdef object receiver
    cdef object connector
    cdef object disconnected
    cdef public bint connected
    cpdef connect(self)
    cpdef send(self, message, token, callback)
    cpdef close(self)