from collections import deque

class RopeBuffer(object):
	"""docstring for Rope"""
	def __init__(self):
		super(RopeBuffer, self).__init__()
		self.ropes = deque()
		self.i = 0
		self.len = 0

	def add(self, data):
		self.ropes.append(data)
		self.len += len(data)

	def _read(self, length):
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

	def read(self, length=-1):
		if length == -1:
			length = self.len
		assert length <= self.len
		if length < len(self.ropes[0]) - self.i:
			data = self.ropes[0][self.i:self.i+length]
			self.i += length
			self.len -= length
			return data
		else:
			return self._read(length)


def main():
	b = RopeBuffer()
	b.add('he')
	b.add('llo')
	b.add(' ')
	b.add('world')

	assert b.read(5) == 'hello'
	assert b.read(6) == ' world'
	assert b.len == 0

	# b = RopeBuffer()
	b.add('he')
	b.add('llo')
	b.add(' ')
	b.add('world')
	assert b.read() == 'hello world'
	assert b.len == 0

if __name__ == '__main__':
	main()