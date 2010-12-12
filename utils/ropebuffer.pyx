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
			if length < len(self.ropes[0]) - self.i:
				fragment = self.ropes[0][self.i:self.i+length]
				self.i += length
			else:
				fragment = self.ropes[0][self.i:]
				self.ropes.popleft()
				self.i = 0
			length -= len(fragment)
			fragments.append(fragment)
		data = ''.join(fragments)
		self.len -= len(data)
		assert data
		return data

	cpdef read(self, int length):
		assert length <= self.len
		if length < len(self.ropes[0]) - self.i:
			data = self.ropes[0][self.i:self.i+length]
			self.i += length
			self.len -= length
			return data
		else:
			return self._read(length)
