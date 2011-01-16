__all__ = ['Channel', 'DisconnectedException']

import socket
from collections import deque
import struct

from ropebuffer cimport RopeBuffer
from ropebuffer import RopeBuffer

from syncless import coio

import logging

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
	def __init__(self, socket=None):
		super(Channel, self).__init__()
		self.socket = socket
		self.buffer = RopeBuffer()
		self.send_buffer = deque()
		self.pack = struct.pack
		self.unpack = struct.unpack
		self.header_spec = '!L'

	cpdef connect(self, listener):
		s = coio.nbsocket(socket.AF_INET, socket.SOCK_STREAM)
		s.connect(listener)
		self.socket = s

	cpdef send(self, message):
		if isinstance(message, str) or isinstance(message, buffer):
			self.send_buffer.append(self.pack(self.header_spec, len(message)))
			self.send_buffer.append(message)
		else:
			self.send_buffer.append(self.pack(self.header_spec, sum(len(fragment) for fragment in message)))
			for fragment in message:
				self.send_buffer.append(fragment)

	cpdef flush(self):
		if self.flushing:
			raise Exception('channel.flush() reentered!')
		self.flushing = True
		cdef object first_string
		cdef unsigned int data_len, sent, next_len
		cdef object strings, next_string
		cdef unsigned int max_payload = 1024*128
		try:
			while self.send_buffer:
				first_string = self.send_buffer.popleft()
				strings = deque((str(first_string),))
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
					strings.append(str(next_string))
					self.send_buffer.popleft()

				# join strings, if necessary
				if len(strings) == 1:
					data = strings[0]
				else:
					data = ''.join(strings)

				self.socket.sendall(data)
		except socket.error:
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
				return ''
			while self.buffer.len < size:
				self.buffer.add(read(self.socket))
			message = self.buffer.read(size)
			return message
		except socket.error:
			raise DisconnectedException()

	cpdef close(self):
		if self.socket:
            # self.send('')
            # self.flush()
			try:
				self.socket.close()
			except socket.error:
				raise DisconnectedException()
			self.socket = None
