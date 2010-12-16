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

cdef read(s, b=1024*16):
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

	cpdef send(self, message):
		try:
			self.send_buffer.append(self.pack(self.header_spec, len(message)))
			self.send_buffer.append(message)
		except IOError:
			raise DisconnectedException()

	cpdef flush(self):
		if self.flushing:
			raise Exception('channel.flush() reentered!')
		self.flushing = True
		cdef object first_string
		cdef unsigned int data_len, sent, next_len
		cdef object strings, next_string
		cdef unsigned int max_payload = 4096
		try:
			while self.send_buffer:
				first_string = self.send_buffer.popleft()
				strings = deque((first_string,))
				data_len = len(first_string)
				next_len = 0
				next_string = None

				# get more data strings from send buffer
				while self.send_buffer:
					next_string = self.send_buffer[0]
					next_len = len(next_string)
					if data_len + next_len > max_payload:
						break
					data_len += next_len
					strings.append(next_string)
					self.send_buffer.popleft()

				# join strings, if necessary
				if len(strings) == 1:
					data = strings[0]
				else:
					data = ''.join(strings)

				self.socket.sendall(data)

		except IOError:
			raise DisconnectedException()
		finally:
			self.flushing = False

	cpdef recv(self):
		cdef unsigned int size
		try:
			while self.buffer.len < 4:
				self.buffer.add(read(self.socket))
			size = self.unpack(self.header_spec, self.buffer.read(4))[0]
			if not size:
				return None
			while self.buffer.len < size:
				self.buffer.add(read(self.socket))
			message = self.buffer.read(size)
			return message
		except IOError:
			raise DisconnectedException()

	cpdef close(self):
		self.send('')
		self.flush()
