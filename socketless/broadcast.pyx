# -*- Mode: Python; tab-width: 4; indent-tabs-mode: nil; -*-

__all__ = ['Broadcast']

from messenger cimport Messenger

from syncless.util import Queue

cdef class Broadcast:
    """docstring for Broadcast"""
    def __init__(self, messengers):
        super(Broadcast, self).__init__()
        self.messengers = messengers
        self.q = Queue()

    cpdef send(self, message):
        """docstring for send"""
        cdef Messenger messenger
        cdef object token
        cdef object _messenger
        for token, _messenger in self.messengers:
            messenger = _messenger
            messenger.send(message, token, self.q)
        replies = [self.q.popleft() for i in xrange(len(self.messengers))]
        return replies
