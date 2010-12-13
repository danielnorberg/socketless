from utils.ropebuffer cimport RopeBuffer
from utils.ropebuffer import RopeBuffer
import struct

from collections import deque

import types

cdef extern from "stdint.h":
	ctypedef unsigned int uint32_t

cdef extern from "arpa/inet.h":
	cdef unsigned int htonl(uint32_t x)
	cdef unsigned int ntohl(uint32_t x)

class DisconnectedException(BaseException):
	pass

cdef read(s, b=1024):
	data = s.recv(b)
	if not data:
		raise DisconnectedException()
	return data

cdef class Channel:
	def __init__(self, socket):
		super(Channel, self).__init__()
		self.socket = socket
		self.buffer = RopeBuffer()
		self.send_buffer = deque()
		self.pack = struct.pack
		self.unpack = struct.unpack
		self.header_spec = '!L'

	cdef send(self, message):
		# cdef unsigned int message_length = htonl(len(message))
		# cdef char header[5];
		try:
			self.send_buffer.append(self.pack(self.header_spec, len(message)))
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
			size = self.unpack(self.header_spec, self.buffer.read(4))[0]
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

