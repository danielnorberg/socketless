# -*- Mode: Python; tab-width: 4; indent-tabs-mode: nil; -*-

__all__ = ['RopeBuffer']

from collections import deque

cdef class RopeBuffer:
    def __init__(self):
        self.ropes = deque()
        self.i = 0
        self.len = 0

    cpdef add(self, data):
        self.ropes.append(data)
        self.len += len(data)

    cpdef _read(self, int length):
        fragments = []
        while length:
            head = self.ropes[0]
            if length < len(head) - self.i:
                fragment = head[self.i:self.i+length]
                self.i += length
            else:
                fragment = head[self.i:]
                self.ropes.popleft()
                self.i = 0
            length -= len(fragment)
            fragments.append(fragment)
        data = ''.join(fragments)
        self.len -= len(data)
        return data

    cpdef read(self, int length):
        assert self.len
        assert length <= self.len
        head = self.ropes[0]
        if length < len(head) - self.i:
            data = head[self.i:self.i+length]
            self.i += length
            self.len -= length
        else:
            data = self._read(length)
        return data

    cpdef drain(self):
        return self.read(self.len)
