from utils.ropebuffer import RopeBuffer
import struct

from collections import deque

class DisconnectedException(BaseException):
	pass

cdef read(s, b=1024):
	data = s.recv(b)
	if not data:
		raise DisconnectedException()
	return data

cdef class Channel:
	cdef object socket
	cdef object buffer
	cdef object send_buffer
	def __init__(self, socket):
		super(Channel, self).__init__()
		self.socket = socket
		self.buffer = RopeBuffer()
		self.send_buffer = deque()

	cpdef send(self, message):
		try:
			self.send_buffer.append(struct.pack('!L', len(message)))
			self.send_buffer.append(message)
		except IOError:
			raise DisconnectedException()

	cpdef flush(self):
		try:
			if self.send_buffer:
				data = ''.join(self.send_buffer)
				self.send_buffer = deque()
				sent = 0
				while sent < len(data):
					sent += self.socket.send(data[sent:])
		except IOError:
			raise DisconnectedException()

	cpdef recv(self):
		cdef unsigned int size
		try:
			while self.buffer.len < 4:
				self.flush()
				data = read(self.socket)
				self.buffer.add(data)
			size = struct.unpack('!L', self.buffer.read(4))[0]
			if not size:
				self.flush()
				return None
			while self.buffer.len < size:
				self.flush()
				self.buffer.add(read(self.socket))
			message = self.buffer.read(size)
			return message
		except IOError:
			raise DisconnectedException()

	cpdef close(self):
		self.send('')
		self.flush()

