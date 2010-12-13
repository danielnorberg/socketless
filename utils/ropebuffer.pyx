from collections import deque

# cdef validate(rb):
# 	cdef int clen = 0
# 	for r in rb.ropes:
# 		clen += len(r)
# 	clen -= rb.i
# 	assert clen == rb.len

cdef class RopeBuffer:
	def __init__(self):
		self.ropes = deque()
		self.i = 0
		self.len = 0

	cpdef add(self, data):
		self.ropes.append(data)
		self.len += len(data)
		# validate(self)

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
		# assert data
		return data

	cpdef read(self, int length):
		assert self.len
		assert length <= self.len
		# print length, self.len
		head = self.ropes[0]
		if length < len(head) - self.i:
			data = head[self.i:self.i+length]
			self.i += length
			self.len -= length
		else:
			data = self._read(length)
		# assert len(data) == length
		# validate(self)
		return data

	cpdef drain(self):
		return self.read(self.len)
